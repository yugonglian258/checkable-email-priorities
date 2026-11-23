"""Lab 3: local rule-based prototype, baseline and revised paths.

Run: python 04_triage_prototype.py --version v1 --case A
     python 04_triage_prototype.py --version v1 --case B
     python 04_triage_prototype.py --version v2 --case B --choice Later

No network, email account, external model or third-party package is required.
Fixture 'expected' fields are evaluation labels and never read by classify().
"""
import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def response(thread, label, reason, extraction, evidence, question=None):
    return {
        "thread_id": thread["id"],
        "subject": thread["subject"],
        "suggestion": label,
        "extracted": extraction,
        "evidence": evidence,
        "reason": reason,
        "clarification": question,
        "choices": ["Today", "Later", "I don't know"] if question else ["Confirm", "Today", "Later"],
        "scope": "Only this thread's label; email stays in the inbox. No reply is sent.",
        "capability": "Local rule-based demonstration, not a general language-understanding model.",
    }


def classify(thread, now, version):
    """Read message fields only; do not consult the test oracle."""
    latest = thread.get("latest", "")
    quote = thread.get("quoted", "")
    if version == "v1":
        # Baseline weakness: flattens provenance and checks day/month without year.
        combined = latest + "\n" + quote
        lower = combined.lower()
        marker = now.strftime("%d %B").lower()
        date_hit = "today" in lower or marker in lower
        label = "ACTION_TODAY" if date_hit else "NOT_TODAY"
        return response(thread, label,
                        "Keyword/date match in combined thread" if date_hit else "No current-day keyword matched",
                        {"date_marker": marker if marker in lower else ("today" if "today" in lower else None),
                         "source_provenance": "latest and quoted text merged; year not validated"},
                        {"source": "combined thread", "text": combined.strip()})

    question = "When do you need to act on this thread: Today, Later, or I don't know?"
    extracted = {"source": "latest message only", "quote_used_for_deadline": False,
                 "request_found": False, "deadline": None}
    evidence = {"source": "latest", "received": thread.get("latest_received"), "text": latest}
    if not isinstance(latest, str) or not latest.strip():
        return response(thread, "NEEDS_REVIEW", "Latest message is missing; no safe inference.",
                        extracted, evidence, "Open the original message or provide the missing latest text.")
    lower = latest.lower()
    # Explicitly limited phrase matcher; it does not resolve negation generally.
    if "no action needed" in lower:
        return response(thread, "NOT_TODAY", "Latest message explicitly says no action is needed.",
                        extracted, evidence)
    extracted["request_found"] = bool(re.search(r"\b(confirm|send|reply|submit)\b", lower))
    received = thread.get("latest_received", "")
    try:
        received_dt = datetime.fromisoformat(received)
        if received_dt.utcoffset() is None or received_dt > now:
            raise ValueError("Missing offset or future timestamp")
    except (TypeError, ValueError):
        return response(thread, "NEEDS_REVIEW", "Message timestamp is missing or invalid.",
                        extracted, evidence, "Check the original message timestamp before choosing a priority.")
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", latest)
    try:
        parsed_dates = [datetime.strptime(s, "%Y-%m-%d").date() for s in dates]
    except ValueError:
        return response(thread, "NEEDS_REVIEW", "An explicit date could not be validated.",
                        extracted, evidence, question)
    if re.search(r"\btoday\b", lower):
        # Relative dates are anchored to the message date, not blindly to run time.
        parsed_dates.append(received_dt.date())
    if len(set(parsed_dates)) > 1:
        return response(thread, "NEEDS_REVIEW", "Multiple inconsistent dates in the latest message.",
                        extracted, evidence, question)
    if not extracted["request_found"] or not parsed_dates:
        return response(thread, "NEEDS_REVIEW", "Current request or deadline is missing/unsupported; do not guess.",
                        extracted, evidence, question)
    deadline = parsed_dates[0]
    extracted["deadline"] = deadline.isoformat()
    if deadline < now.date():
        return response(thread, "NEEDS_REVIEW", "The latest deadline is already past; urgency needs confirmation.",
                        extracted, evidence, question)
    label = "ACTION_TODAY" if deadline == now.date() else "NOT_TODAY"
    return response(thread, label, "Validated latest-message deadline compared with the fixed local date.",
                    extracted, evidence)


class LabelSession:
    """Implemented in-memory label changes and undo; no mailbox mutation."""
    def __init__(self):
        self.labels = {}
        self.history = []

    def choose(self, result, choice):
        before = copy.deepcopy(self.labels)
        if choice == "I don't know":
            return {"state": "NEEDS_REVIEW", "changed": False, "next": "Open original message; no label saved."}
        mapping = {"Today": "ACTION_TODAY", "Later": "NOT_TODAY"}
        label = result["suggestion"] if choice == "Confirm" else mapping.get(choice)
        if label not in ("ACTION_TODAY", "NOT_TODAY"):
            raise ValueError("A review state cannot be confirmed as a resolved priority.")
        self.history.append(before)
        self.labels[result["thread_id"]] = label
        return {"state": label, "changed": True, "thread_id": result["thread_id"],
                "message": "Only this thread changed in the local session. Email retained. Undo available.",
                "labels": copy.deepcopy(self.labels)}

    def undo(self):
        if not self.history:
            return {"changed": False, "message": "Nothing to undo."}
        self.labels = self.history.pop()
        return {"changed": True, "message": "Previous local labels restored.", "labels": copy.deepcopy(self.labels)}


def load_inputs(path=None):
    return json.loads(Path(path or HERE / "03_test_inputs.json").read_text(encoding="utf-8"))


def run_case(data, case_name, version, choice=None):
    case = data["cases"][case_name]
    now = datetime.fromisoformat(data["now"])
    # Oracle fields are deliberately removed before processing.
    inputs = [{k: v for k, v in t.items() if k != "expected"} for t in case["threads"]]
    results = [classify(t, now, version) for t in inputs]
    session = LabelSession()
    out = {"version": version, "case": case_name, "request": case["request"],
           "clock": data["now"], "timezone": data["timezone"],
           "input_threads": inputs, "results": results,
           "labels_before_user_choice": copy.deepcopy(session.labels)}
    if choice:
        out["scripted_user_choice"] = choice
        out["feedback"] = session.choose(results[0], choice)
        out["undo_feedback"] = session.undo()
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=["v1", "v2"], default="v2")
    parser.add_argument("--case", choices=["A", "B"], default="A")
    parser.add_argument("--choice", choices=["Confirm", "Today", "Later", "I don't know"])
    args = parser.parse_args()
    try:
        print(json.dumps(run_case(load_inputs(), args.case, args.version, args.choice), indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "UNAVAILABLE", "error": str(error),
                          "message": "Cannot read or validate local data. No priority labels applied; use the original inbox."}, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

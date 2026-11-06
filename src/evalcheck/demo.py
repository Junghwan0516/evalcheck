"""Intentionally constructed examples, never presented as observed benchmarks."""
from .core import AuditConfig, audit
from .io import write_json, write_jsonl
from .report import write_report


def make_demo(directory,*,lang="en"):
    directory.mkdir(parents=True, exist_ok=True)
    train = [
        {"text": "Plants convert sunlight into chemical energy through photosynthesis.", "label": "correct", "question_id": "biology-01"},
        {"text": "The electric current increases when resistance decreases at fixed voltage.", "label": "correct", "question_id": "physics-02"},
        {"text": "Water boils at 100 degrees Celsius at standard atmospheric pressure.", "label": "correct", "question_id": "chemistry-03"},
        {"text": "An enzyme lowers the activation energy of a reaction.", "label": "correct", "question_id": "biology-04"},
        {"text": "Mass is measured in kilograms.", "label": "correct", "question_id": "physics-05"},
        {"text": "The nucleus stores most of a cell's genetic information.", "label": "correct", "question_id": "biology-06"},
        {"text": "A catalyst is completely consumed in every reaction.", "label": "incorrect", "question_id": "chemistry-07"},
        {"text": "An object at rest has zero velocity relative to the observer.", "label": "correct", "question_id": "physics-08"},
    ]
    test = [
        {"text": "  PLANTS convert sunlight into chemical energy through photosynthesis. ", "label": "correct", "question_id": "biology-01"},
        {"text": "The electric current increases when resistance decreases at a fixed voltage.", "label": "correct", "question_id": "physics-09"},
        {"text": "Water boils at 100 degrees Celsius at standard atmospheric pressure.", "label": "incorrect", "question_id": "chemistry-03"},
        {"text": "Enzymes make some chemical reactions proceed faster.", "label": "correct", "question_id": "biology-04"},
        {"text": "Mitochondria participate in cellular respiration.", "label": "correct", "question_id": "biology-10"},
        {"text": "The Moon generates sunlight through nuclear fusion.", "label": "incorrect", "question_id": "astronomy-11"},
    ]
    config = AuditConfig(group="question_id")
    result = audit({"train": train, "test": test}, config)
    write_jsonl(directory / "train.jsonl", train)
    write_jsonl(directory / "test.jsonl", test)
    write_json(directory / "audit.json", result)
    write_report(result, directory / "report.html",lang=lang)
    return result

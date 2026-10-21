from config.llm import langfuse
from evals.cases import CASES

DATASET_NAME = "northwind-text-to-sql"


def upload():
    langfuse.create_dataset(
        name=DATASET_NAME,
        description="Northwind questions with gold SQL",
    )
    for i, tc in enumerate(CASES, 1):
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME,
            id=f"case-{i}",
            input={"question": tc["question"]},
            expected_output={"gold_sql": tc["gold_sql"]},
        )
    langfuse.flush()
    print(f"Uploaded {len(CASES)} items to '{DATASET_NAME}'")


if __name__ == "__main__":
    upload()
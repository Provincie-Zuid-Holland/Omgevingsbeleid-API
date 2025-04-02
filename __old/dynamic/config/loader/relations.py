from typing import List


def relations_loader(config: dict) -> List[str]:
    relations: List[str] = []

    for relation_id, data in config.items():
        relations.append(relation_id)

    return relations

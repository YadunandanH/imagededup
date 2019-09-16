import os
import itertools
from typing import Dict

from imagededup.handlers.metrics.classification import classification_metrics
from imagededup.handlers.metrics.information_retrieval import (
    mean_metric,
    get_all_metrics,
)
from imagededup.utils.logger import return_logger

logger = return_logger(__name__, os.getcwd())


def _transpose_checker(mapping):
    """
    Check for the given dictionary that transpose relationship holds.

    Args:
        mapping: Dictionary respresenting a mapping of filenames to the list of respectove duplicate filenames.
    """
    for key, val in mapping.items():
        # check for each value in the list if the key is present as its value
        for v in val:
            assert key in mapping[v], (
                f'Transpose relationship violated, file {key} not present as a duplicate for file {v} in the provided'
                f' mapping dictionary'
            )


def _check_map_correctness(ground_truth_map: Dict, retrieved_map: Dict):
    """
    Perform following validation checks for both ground truth and retrieved maps:
    - Each duplicates filename should be one of the keys (no files that are not keys of the map)
    - Transpose relationships are present. Eg: if 'file1.jpg' is a duplicate for 'file2.jpg', then both relationships
    should be present in the respective map i.e., {'file1.jpg': ['file2.jpg'], 'file2.jpg': ['file1.jpg']}
    - Ground truth as well as retrieved map have exactly the same keys.

    Args:
        ground_truth_map: A dictionary representing ground truth with filenames as key and a list of duplicate filenames
        as value.
        retrieved_map: A dictionary representing retrieved duplicates with filenames as key and a list of retrieved
        duplicate filenames as value.
    """
    logger.info('Validating ground truth map ..')
    ground_truth_keys_set = set(ground_truth_map.keys())
    ground_truth_val_set = set(itertools.chain(*list(ground_truth_map.values())))
    assert (
        len(ground_truth_val_set.difference(ground_truth_keys_set)) == 0
    ), 'Ground truth map validation failed, Ground truth has filenames that are not in the key filename of the map!'
    _transpose_checker(
        ground_truth_map
    )  # transpose relationships important for Information Retrieval metrics
    logger.info('Ground truth map validated')

    logger.info('Validating retrieved map ..')
    duplicate_map_keys_set = set(retrieved_map.keys())
    duplicate_val_set = set(itertools.chain(*list(retrieved_map.values())))
    assert (
        len(duplicate_val_set.difference(duplicate_map_keys_set)) == 0
    ), 'Retrieved map validation failed, Retrieved map has filenames that are not in the key filename of the map!'
    _transpose_checker(retrieved_map)
    logger.info('Duplicate map validated')

    logger.info('Validating ground truth map and retrieved map consistency..')
    if not ground_truth_keys_set == duplicate_map_keys_set:
        diff = ground_truth_keys_set.symmetric_difference(duplicate_map_keys_set)
        raise Exception(
            f'Please ensure that ground truth and retrieved map have the same keys!'
            f' Following keys uncommon between ground truth and retrieved maps:\n{diff}'
        )
    logger.info('Ground truth map and retrieved map found to be consistent.')


def evaluate(
    ground_truth_map: Dict = None, duplicate_map: Dict = None, metric: str = 'all'
):
    metric = metric.lower()
    _check_map_correctness(ground_truth_map, duplicate_map)

    if metric in ['map', 'ndcg', 'jaccard']:
        return {metric: mean_metric(ground_truth_map, duplicate_map, metric=metric)}
    elif metric == 'classification':
        return classification_metrics(ground_truth_map, duplicate_map)
    elif metric == 'all':
        ir_metrics = get_all_metrics(ground_truth_map, duplicate_map)
        class_metrics = classification_metrics(ground_truth_map, duplicate_map)
        ir_metrics.update(class_metrics)
        return ir_metrics
    else:
        raise ValueError(
            'Acceptable metrics are: \'map\', \'ndcg\', \'jaccard\', \'classification\', \'all\''
        )

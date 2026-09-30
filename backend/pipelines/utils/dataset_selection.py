def select_datasets(config, dataset_names=None, group=None):
    datasets = config.get("datasets", []) + config.get("postal_code_datasets", [])

    if dataset_names:
        configured_names = {dataset["name"] for dataset in datasets}
        unknown_names = set(dataset_names) - configured_names
        if unknown_names:
            raise ValueError(f"Unknown dataset(s): {', '.join(sorted(unknown_names))}")
        datasets = [dataset for dataset in datasets if dataset["name"] in dataset_names]

    if group:
        datasets = [dataset for dataset in datasets if dataset.get("group") == group]
        if not datasets:
            raise ValueError(f"No datasets configured for group '{group}'")

    return datasets
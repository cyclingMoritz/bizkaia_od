
def get_unique_options(df, id_col, name_col):
    """Return unique IDs and names from DataFrame."""
    ids = df[id_col].explode().unique().tolist()
    names = df[name_col].explode().unique().tolist()
    return ids, names

def sync_selection(df, selected_ids, selected_names, id_col, name_col):
    """
    Sync selections between an ID column and a Name column.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the columns to sync.
    selected_ids : list
        List of user-selected IDs.
    selected_names : list
        List of user-selected Names.
    id_col : str
        Name of the column representing the IDs.
    name_col : str
        Name of the column representing the Names.

    Returns
    -------
    all_ids : set
        Set of all selected IDs, including those inferred from names.
    all_names : set
        Set of all selected names, including those inferred from IDs.
    """
    id_to_name = dict(zip(df[id_col], df[name_col]))
    name_to_id = dict(zip(df[name_col], df[id_col]))

    # Keep only valid selections that exist in the mappings
    all_ids = set(selected_ids)
    all_ids.update(name_to_id[name] for name in selected_names if name in name_to_id)

    all_names = set(selected_names)
    all_names.update(id_to_name[i] for i in selected_ids if i in id_to_name)

    return all_ids, all_names



def filter_datasets_by_lines(lines_gdf, stops_gdf, vehicles_df, selected_line_ids):
    selected_lines = lines_gdf[lines_gdf["line_id"].isin(selected_line_ids)]
    selected_stops = stops_gdf[stops_gdf["line_id"].isin(selected_line_ids)]
    vehicles_bus_filtered = vehicles_df[vehicles_df["line_id"].isin(selected_line_ids)]
    return selected_lines, selected_stops, vehicles_bus_filtered
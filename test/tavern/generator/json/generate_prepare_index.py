import argparse

class Index:
    def __init__(self):
        """Initialize an Index instance with default values."""
        self.created = "2026-01-01 00:00:00"
        self.updated = "2026-01-01 00:00:00"
        self.id = 0
        self.parent = 0
        self.position = 0
        self.index_name = ""
        self.index_name_english = ""
        self.index_link_name = ""
        self.index_link_name_english = ""
        self.harvest_spec = ""
        self.index_link_enabled = False
        self.comment = ""
        self.more_check = False
        self.display_no = 5
        self.harvest_public_state = False
        self.display_format = "1"
        self.image_name = ""
        self.public_state = False
        self.public_date = None
        self.recursive_public_state = False
        self.rss_status = False
        self.coverpage_state = False
        self.recursive_coverpage_check = False
        self.browsing_role = "3,-98,-99"
        self.recursive_browsing_role = False
        self.contribute_role = "3,4,-98"
        self.recursive_contribute_role = False
        self.browsing_group = ""
        self.recursive_browsing_group = False
        self.contribute_group = ""
        self.recursive_contribute_group = False
        self.owner_user_id = 1
        self.item_custom_sort = {}
        self.biblio_flag = False
        self.online_issn = ""
        self.cnri = None
        self.index_url = None
        self.is_deleted = False

    def set(self, **kwargs):
        """Set attributes of the Index instance.

        Args:
            **kwargs: Key-value pairs of attributes to set.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def create_query(self):
        """Generate an SQL INSERT query for the Index instance.

        Returns:
            str: SQL INSERT query string.
        """
        columns = [str(attr) for attr in self.__dict__.keys()]
        values = []
        for col in columns:
            val = getattr(self, col)
            if isinstance(val, str):
                values.append(f"'{val.replace("'", "''")}'")
            elif isinstance(val, bool):
                values.append("'true'" if val else "'false'")
            elif val is None:
                values.append("NULL")
            elif isinstance(val, dict):
                values.append(f"'{str(val).replace("'", "''")}'")
            else:
                values.append(str(val))
        columns_str = ", ".join(columns)
        values_str = ", ".join(values)
        return f"INSERT INTO index ({columns_str}) VALUES ({values_str});"


def create_index(
    depth, num, current_level = 1, parent_id = 0, before_id = 0, adjust_position = -1
):
    """Recursively create a list of Index instances.

    Args:
        depth(int): Depth of the index hierarchy.
        num(int): Number of indices per level.
        current_level(int, optional): Current level in the hierarchy. Defaults to 1.
        parent_id(int, optional): Parent index ID. Defaults to 0.
        before_id(int, optional): ID of the last created index. Defaults to 0.
        adjust_position(int, optional): Adjustment for the position value. Defaults to -1.

    Returns:
        list[Index]: List of created Index instances.
    """
    indices = []
    id = before_id + 1
    if current_level > depth:
        return indices
    for i in range(1, num + 1):
        index = Index()
        params = {
            "id": id,
            "parent": parent_id,
            "position": i + adjust_position,
            "index_name": f"Index_L{current_level}_N{i}",
            "index_name_english": f"Index_L{current_level}_N{i}_EN",
            "index_link_name": f"Index_L{current_level}_N{i}_Link",
            "index_link_name_english": f"Index_L{current_level}_N{i}_Link_EN",
        }
        index.set(**params)
        indices.append(index)
        child_indices = create_index(depth, num, current_level + 1, id, id)
        indices.extend(child_indices)
        id += len(child_indices) + 1
    return indices


def main(hierarchy_depth, num_indices_per_level):
    """Generate SQL queries to prepare index data and save to a file.

    Args:
        hierarchy_depth(int): Depth of the index hierarchy.
        num_indices_per_level(int): Number of indices per level.
    """
    indices = create_index(hierarchy_depth, num_indices_per_level, before_id=100, adjust_position=2)

    with open("prepare_data/prepare_index.sql", "w", encoding="utf-8") as f:
        query = [index.create_query() for index in indices]
        f.write("\n".join(query))


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate SQL to prepare index data.")
    parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=2,
        help="Hierarchy depth of indices (default: 2)",
    )
    parser.add_argument(
        "-n",
        "--num-per-level",
        type=int,
        default=3,
        help="Number of indices per level (default: 3)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    hierarchy_depth = args.depth
    num_indices_per_level = args.num_per_level
    main(hierarchy_depth, num_indices_per_level)

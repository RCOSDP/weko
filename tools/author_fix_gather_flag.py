"""
ログ例
* データベース名,WEKO_ID(authors.id),authors.gather_flag(修正前),authors.json->gather_flag(修正前),WEKO_ID,authors.gather_flag(修正後)
"""
import csv, psycopg2, sys, traceback
from os import getenv
from os.path import dirname, join

TARGET_LIST_FILENAME = 'target_list.tsv'
INDEX_NAME = '-authors-author-v1.0.0'
GATHER_FLAG_BEFORE = 1
GATHER_FLAG_AFTER = 0

def group_by_index(filename):
    grouped_data = {}
    with open(filename, "r") as f:
        reader = csv.reader(f, delimiter='\t')
        l = [row for row in reader]
        for ll in l[1:]:
            db_name = ll[0].replace(INDEX_NAME, '')
            if not db_name in list(grouped_data):
                grouped_data[db_name] = []
            grouped_data[db_name].append(ll[1])
    return grouped_data

def get_connection(db_name):
    return psycopg2.connect(
        database=db_name,
        user=getenv('INVENIO_POSTGRESQL_DBUSER'),
        password=getenv('INVENIO_POSTGRESQL_DBPASS'),
        host=getenv('INVENIO_POSTGRESQL_HOST'),
        port=5432,
        connect_timeout=10
    )

def fix_gather_flag(grouped_data):
    try:
        conn = []
        cur = []
        for i, (db_name, weko_id_list) in enumerate(grouped_data.items()):
            conn.append(get_connection(db_name))
            cur.append(conn[i].cursor())

            stmt_formats = ','.join(['%s'] * len(weko_id_list))
            cur[i].execute('SELECT id, gather_flg, json FROM authors WHERE id IN (%s)'%stmt_formats, tuple(weko_id_list))
            authors = cur[i].fetchall()

            for author in authors:
                if author[1] == GATHER_FLAG_BEFORE and author[2].get('gather_flg') == GATHER_FLAG_AFTER:
                    cur[i].execute(f'UPDATE authors SET updated = CURRENT_TIMESTAMP, gather_flg = {GATHER_FLAG_AFTER} WHERE id = {author[0]}')
                    print(f"{db_name},{author[0]},{author[1]},{author[2].get('gather_flg')},{author[0]},{GATHER_FLAG_AFTER}")

        for i in range(len(conn)):
            conn[i].commit()

    except:
        for i in range(len(conn)):
            conn[i].rollback()
        print(traceback.print_exc())

    finally:
        for i in range(len(conn)):
            cur[i].close()
            conn[i].close()

if __name__ == '__main__':
    args = sys.argv

    input_file_path = args[1] if len(args) == 2 else join(dirname(__file__), TARGET_LIST_FILENAME)
    grouped_data = group_by_index(input_file_path)

    fix_gather_flag(grouped_data)

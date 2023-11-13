from weko_authors.api import WekoAuthors
from weko_authors.models import Authors
from invenio_db import db
from sqlalchemy.sql.expression import func
import random
import settings


def main():
    for i in range(settings.AUTHOR_LIMIT):
        create_author()
        if i % 1000 == 0 and i != 0:
            print('{} author created'.format(i))

def create_author():
    en_code = 'en'
    ja_code = 'ja'
    max_author_id = db.session.query(func.max(Authors.id)).one_or_none()[0]
    if max_author_id:
        author_id = max_author_id + 1
    else:
        author_id = 1
    family_name = 'last_name_{0:08d}'.format(author_id)
    first_name = 'first_name_{0:08d}'.format(author_id)

    id1 = '{0:04d}'.format(random.randint(0, 9999))
    id2 = '{0:04d}'.format(random.randint(0, 9999))
    id3 = '{0:04d}'.format(random.randint(0, 9999))
    id4 = '{0:04d}'.format(random.randint(0, 9999))
    orcid = '{}-{}-{}-{}'.format(id1, id2, id3, id4)

    data = {
        "authorIdInfo": [{
            "idType" : "2",
            "authorIdShowFlg" : "true",
            "authorId" : orcid
		}],
        "authorNameInfo": [
            {
                "familyName": '{}_{}'.format(en_code, family_name),
                "firstName": '{}_{}'.format(en_code, first_name),
                "language": en_code,
                "nameFormat": "familyNmAndNm",
                "nameShowFlg": "true"
            },
            {
                "familyName": '{}_{}'.format(ja_code, family_name),
                "firstName": '{}_{}'.format(ja_code, first_name),
                "language": ja_code,
                "nameFormat": "familyNmAndNm",
                "nameShowFlg": "true"
            }
        ],
        "emailInfo": [{
            "email": "author_{0:08d}@example.org".format(author_id)
        }],
        "id": None,
        "is_deleted": False
    }

    try:
        WekoAuthors.create(data)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)


if __name__ == '__main__':
    main()

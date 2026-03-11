from invenio_db import db
from weko_authors.utils import check_email_existed
from weko_records.models import FeedbackMailList
from flask import current_app

def main():
    try:
        current_app.logger.info('==================== Update feedback mail list to db be starting.')
        data = FeedbackMailList.query.all()
        for d in data:
            mail_list = []
            author_id_list = d.account_author.split(',') \
                if d.account_author else []
            for m in d.mail_list:
                author_id = m.get("author_id")
                email = m.get("email")
                if author_id:
                    author_id_list.append(author_id)
                elif email:
                    email_checked = check_email_existed(email)
                    author_id = email_checked.get("author_id")
                    if author_id:
                        author_id_list.append(author_id)
                    else:
                        mail_list.append({"email": email})
            d.mail_list = mail_list
            d.account_author = ",".join(list(set(author_id_list)))
            db.session.merge(d)
        fixed_ids = [d.id for d in data]
        for i in fixed_ids:
            current_app.logger.info(f"[FIX] feedback_mail_list:{i}")
        db.session.commit()
        current_app.logger.info('==================== Update feedback mail list to db is success.')
    except Exception as e:
        db.session.rollback()
        import traceback
        current_app.logger.info('==================== Update feedback mail list to db is fail.')
        current_app.logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()
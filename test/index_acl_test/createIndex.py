from weko_index_tree.models import Index
from invenio_db import db

MAX_DEPTH=3
idx = 0


def createIndex(idx,_parent = 0,depth = 0):
    """Create all pattern index for testing.

    Args:
        idx (_type_): latest index id
        _parent (int, optional): id of parent index. Defaults to 0.
        depth (int, optional): current depth of index. Defaults to 0.

    Returns:
        _type_: latest index id
    Todo:
        make OAI Set
        update redis store for index
    """    
    with db.session.begin_nested():
        idx = idx + 1
        # -99 : Guest
        # -98 : Authenticated 
        pub_oai_guest = Index(id=idx,parent=_parent, 
                              index_name="{}-public-oai-guest-{}".format(depth,idx),index_name_english="{}-public-oai-guest-{}".format(depth,idx),
                              index_link_name="{}-public-oai-guest-{}".format(depth,idx),index_link_name_english="{}-public-oai-guest-{}".format(depth,idx),
                              position=0,public_state=True,harvest_public_state=True, recursive_browsing_role=False,browsing_role = "3,-98,-99")
        idx = idx + 1
        pri_oai_guest = Index(id=idx,parent=_parent, 
                              index_name="{}-private-oai-guest-{}".format(depth,idx),index_name_english="{}-private-oai-guest-{}".format(depth,idx),
                              index_link_name="{}-private-oai-guest-{}".format(depth,idx),index_link_name_english="{}-private-oai-guest-{}".format(depth,idx),
                              position=1, public_state=False,harvest_public_state=True, recursive_browsing_role=False,browsing_role = "3,-98,-99")
        idx = idx + 1
        pub_nooai_guest = Index(id=idx,parent=_parent, 
                                index_name="{}-public-nooai-guest-{}".format(depth,idx),index_name_english="{}-public-nooai-guest-{}".format(depth,idx),
                                index_link_name="{}-public-nooai-guest-{}".format(depth,idx),index_link_name_english="{}-public-nooai-guest-{}".format(depth,idx),
                                position=2, public_state=True,harvest_public_state=False, recursive_browsing_role=False,browsing_role = "3,-98,-99")
        idx = idx + 1
        pri_nooai_guest = Index(id=idx,parent=_parent, 
                                index_name="{}-private-nooai-guest-{}".format(depth,idx),index_name_english="{}-private-nooai-guest-{}".format(depth,idx),
                                index_link_name="{}-private-nooai-guest-{}".format(depth,idx),index_link_name_english="{}-private-nooai-guest-{}".format(depth,idx),
                                position=3,public_state=False,harvest_public_state=False, recursive_browsing_role=False,browsing_role = "3,-98,-99")
        idx = idx + 1
        pub_oai_noguest = Index(id=idx,parent=_parent, 
                                index_name="{}-public-oai-noguest-{}".format(depth,idx),index_name_english="{}-public-oai-noguest-{}".format(depth,idx),
                                index_link_name="{}-public-oai-noguest-{}".format(depth,idx),index_link_name_english="{}-public-oai-noguest-{}".format(depth,idx),
                                position=4,public_state=True,harvest_public_state=True, recursive_browsing_role=False,browsing_role = "3,-98")
        idx = idx + 1
        pri_oai_noguest = Index(id=idx,parent=_parent, 
                                index_name="{}-private-oai-noguest-{}".format(depth,idx),index_name_english="{}-private-oai-noguest-{}".format(depth,idx),
                                index_link_name="{}-private-oai-noguest-{}".format(depth,idx),index_link_name_english="{}-private-oai-noguest-{}".format(depth,idx),
                                position=5, public_state=False,harvest_public_state=True, recursive_browsing_role=False,browsing_role = "3,-98")
        idx = idx + 1
        pub_nooai_noguest = Index(id=idx,parent=_parent, 
                                  index_name="{}-public-nooai-noguest-{}".format(depth,idx),index_name_english="{}-public-nooai-noguest-{}".format(depth,idx),
                                  index_link_name="{}-public-nooai-noguest-{}".format(depth,idx),index_link_name_english="{}-public-nooai-noguest-{}".format(depth,idx),
                                  position=6, public_state=True,harvest_public_state=False, recursive_browsing_role=False,browsing_role = "3,-98")
        idx = idx + 1
        pri_nooai_noguest = Index(id=idx,parent=_parent, 
                                  index_name="{}-private-nooai-noguest-{}".format(depth,idx),index_name_english="{}-private-nooai-noguest-{}".format(depth,idx),
                                  index_link_name="{}-private-nooai-noguest-{}".format(depth,idx),index_link_name_english="{}-private-nooai-noguest-{}".format(depth,idx),
                                  position=7,public_state=False,harvest_public_state=False, recursive_browsing_role=False,browsing_role = "3,-98")
        db.session.add(pub_oai_guest)
        db.session.add(pri_oai_guest)
        db.session.add(pub_nooai_guest)
        db.session.add(pri_nooai_guest)
        db.session.add(pub_oai_noguest)
        db.session.add(pri_oai_noguest)
        db.session.add(pub_nooai_noguest)
        db.session.add(pri_nooai_noguest)
        print(pub_oai_guest.index_name)
        print(pri_oai_guest.index_name)
        print(pub_nooai_guest.index_name)
        print(pri_nooai_guest.index_name)
        print(pub_oai_noguest.index_name)
        print(pri_oai_noguest.index_name)
        print(pub_nooai_noguest.index_name)
        print(pri_nooai_noguest.index_name)
    db.session.commit()
    depth = depth + 1
    if depth < MAX_DEPTH:
        idx = createIndex(idx,pub_oai_guest.id,depth)
        idx = createIndex(idx,pri_oai_guest.id,depth)
        idx = createIndex(idx,pub_nooai_guest.id,depth)
        idx = createIndex(idx,pri_nooai_guest.id,depth)
        idx = createIndex(idx,pub_oai_noguest.id,depth)
        idx = createIndex(idx,pri_oai_noguest.id,depth)
        idx = createIndex(idx,pub_nooai_noguest.id,depth)
        idx = createIndex(idx,pri_nooai_noguest.id,depth)
    return idx
    



def clearTable():
    Index.query.delete()
    db.session.execute("ALTER SEQUENCE index_id_seq RESTART WITH 1")
    db.session.commit()

if __name__ == '__main__':
    clearTable()
    idx = 0
    idx = createIndex(0,0,0)
    
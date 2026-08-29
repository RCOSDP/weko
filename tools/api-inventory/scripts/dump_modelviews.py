from flask import current_app
admin=current_app.extensions['admin'][0]
out=[]
for v in admin._views:
    cls=type(v).__name__
    ep=getattr(v,'endpoint',None)
    model=getattr(getattr(v,'model',None),'__name__',None)
    table=getattr(getattr(v,'model',None),'__tablename__',None)
    can_c=getattr(v,'can_create',None); can_e=getattr(v,'can_edit',None)
    can_d=getattr(v,'can_delete',None); can_x=getattr(v,'can_export',None)
    can_vd=getattr(v,'can_view_details',None)
    exp_list=getattr(v,'column_export_list',None)
    if model:  # ModelView only
        out.append("\t".join(str(x) for x in [ep,cls,model,table,can_c,can_e,can_d,can_x,can_vd,exp_list]))
open("/tmp/mv.tsv","w").write("\n".join(out))
print("ModelViews:",len(out))

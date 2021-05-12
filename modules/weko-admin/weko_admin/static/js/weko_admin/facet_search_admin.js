const {useState, useEffect} = React;
const LABELS = {};
const urlList = window.location.origin + "/admin/facetsearch/";
const MARGIN_TEXT = {marginLeft: "15px"};

(function () {
  // Get all labels.
  let labels = document.getElementsByClassName('facet-search-label');
  for (let i = 0; i < labels.length; i++) {
    LABELS[labels[i].id] = labels[i].value;
  }

  let isEditScreen = ['new', 'edit'].indexOf(LABELS['lblTypeScreen']) != -1;
  ReactDOM.render(
    <Layout isEditScreen={isEditScreen}/>,
    document.getElementById('root')
  )
})();

function Layout({isEditScreen}) {
  let initValue = LABELS['lblInitData'];
  if (isEditScreen) {
    // Create or Edit
    return <FacetSearchLayout {...JSON.parse(initValue)} />;
  } else {
    // Detail or Delete
    return <FacetSearchDetailsLayout {...JSON.parse(initValue)} />;
  }
}

function FacetSearchLayout(
  {
    name_en, name_jp, mapping, active, aggregations, mapping_list
  }
) {
  const [_nameEN, _setNameEN] = useState(name_en);
  const [_nameJP, _setNameJP] = useState(name_jp);
  const [_mapping, _setMapping] = useState(mapping);
  const [_active, _setActive] = useState(active);
  const [_aggregations, _setAggregations] = useState(aggregations);

  function handleSaveFacetSearch() {
    const URL = "/api/admin/facetsearch/save";
    let data = {
      name_en: _nameEN,
      name_jp: _nameJP,
      mapping: _mapping,
      active: _active,
      aggregations: _aggregations
    }
    if (LABELS['lblFacetSearchId']){
      data['id'] = LABELS['lblFacetSearchId'];
    }
    $.ajax({
      url: URL,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.status) {
          console.log(result.msg, 2);
        } else {
          console.log("false");
        }
        window.location.href = urlList;
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  return (
    <div>
      <HeaderComponent/>
      <div className="row">
        <div className="col-sm-12 col-md-12 col-md-12">
          <div className="panel panel-default">
            <div className="panel-body">
              <div className="row">
                <InputTextComponent value={_nameEN} setValue={_setNameEN}
                                    idName={LABELS['lblNameEN']}/>
              </div>
              <div className="row">
                <InputTextComponent value={_nameJP} setValue={_setNameJP}
                                    idName={LABELS['lblNameJP']}/>
              </div>
              <div className="row">
                <div className="form-group row">
                  <label htmlFor={LABELS['lblMapping']} className="col-sm-2 col-form-label"
                         style={MARGIN_TEXT}>{LABELS['lblMapping']}</label>
                  <div className="col-sm-7">
                    <select className="form-control" id={LABELS['lblMapping']}
                            value={_mapping}
                            onChange={e => _setMapping(e.target.value)}>
                      {
                        mapping_list.map((item) =>
                          <option value={item}>{item}</option>)
                      }
                    </select>
                  </div>
                </div>
              </div>
              <div className="row">
                <CustomAggregations aggregations={_aggregations}
                                    setAggregations={_setAggregations}
                                    mappingList={mapping_list}/>
              </div>
              <div className="row">
                <InputRadioComponent value={_active} setValue={_setActive}
                                     idName={LABELS['lblActive']}/>
              </div>
              <div className="row">
                  <div className="form-group row">
                    <div className="col-sm-2" style={MARGIN_TEXT}>
                    </div>
                    <div className="col-sm-7">
                      <button type="button" style={{marginRight: "3px"}}
                              className="btn btn-primary"
                              onClick={handleSaveFacetSearch}>{LABELS['lblSave']}</button>
                      <a href="/admin/facetsearch/" className="btn btn-danger"
                         role="button">{LABELS['lblCancel']}</a>
                    </div>
                  </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function InputTextComponent({value, setValue, idName}) {

  function handleChange(event) {
    event.preventDefault();
    let target = event.target;
    setValue(target.value);
  }

  return (
    <div>
      <div className="form-group row">
        <label htmlFor={idName} className="col-sm-2 col-form-label"
               style={MARGIN_TEXT}> {idName} </label>
        <div className="col-sm-7">
          <input type="text" id={idName} className="form-control" value={value}
                 onChange={handleChange}/>
        </div>
      </div>
    </div>
  )
}

function InputRadioComponent({value, setValue, idName}) {

  function handleChangeDisplay(event) {
    setValue(!value);
  }

  return (
    <div className="form-group">
      <label htmlFor={idName} className="col-sm-2 col-form-label"
             style={MARGIN_TEXT}> {idName}</label>
      <div className="form-group">
        <label className="radio-inline" htmlFor="display">
          <input type="radio" id="display" checked={value === true}
                 onChange={handleChangeDisplay}/>
          {LABELS['lblDisplay']}
        </label>
        <label className="radio-inline" htmlFor="hide">
          <input type="radio" id="hide" checked={value === false}
                 onChange={handleChangeDisplay}/>
          {LABELS['lblHide']}
        </label>
      </div>
    </div>
  )
}

function CustomAggregations({aggregations, setAggregations, mappingList}) {

  const [aggListVal, setAggListVal] = useState('');
  const [aggMapping, setAggMapping] = useState('');
  const [aggValue, setAggValue] = useState('');

  useEffect(function () {
    if (aggregations && aggregations.length > 0) {
      let firstItem = aggregations[0];
      setAggListVal(firstItem['agg_mapping'] + ' - ' + firstItem['agg_value']);
      setAggMapping(firstItem['agg_mapping']);
      setAggValue(firstItem['agg_value']);
    }
  }, [])

  function handleAggListChange(event) {
    event.preventDefault();
    aggregations.map((item) => {
      let oldItem = item['agg_mapping'] + ' - ' + item['agg_value'];
      if (oldItem === event.target.value) {
        setAggMapping(item['agg_mapping']);
        setAggValue(item['agg_value']);
      }
    });
    setAggListVal(event.target.value);
  }

  function handleDeleteAggList(event) {
    // Delete 'Aggregations List'.
    event.preventDefault();
    if (!aggListVal) {
      return;
    }
    // Delete selected item.
    let aggregationsTemp = [];
    aggregations.map((item) => {
      let oldItem = item['agg_mapping'] + ' - ' + item['agg_value'];
      let newItem = aggMapping + ' - ' + aggValue;
      if (oldItem !== newItem) {
        aggregationsTemp.push(item);
      }
    });
    setAggregations(aggregationsTemp);
    // Load first item for 'Aggregations List', 'Aggregation Mapping', 'Aggregation Value'.
    if (!aggregationsTemp || aggregationsTemp.length === 0) {
      setAggMapping('');
      setAggValue('');
      return;
    }
    let firstAggMapping = aggregationsTemp[0]['agg_mapping'];
    let firstAggValue = aggregationsTemp[0]['agg_value'];
    let firstItem = firstAggMapping + ' - ' + firstAggValue;
    setAggListVal(firstItem);
    setAggMapping(firstAggMapping);
    setAggValue(firstAggValue);
  }

  function handleAddAggList(event) {
    // Add 'Aggregations List'.
    event.preventDefault();
    // Check existed item.
    let isExist = false;
    let newItem = aggMapping + ' - ' + aggValue;
    aggregations.map((item) => {
      let oldItem = item['agg_mapping'] + ' - ' + item['agg_value'];
      if (oldItem === newItem) {
        isExist = true;
      }
    });
    if (isExist) {
      alert("Item exist.");
      return;
    }
    // Add new item to 'Aggregations List'.
    setAggregations([...aggregations, {
      agg_mapping: aggMapping,
      agg_value: aggValue
    }]);
    setAggListVal(newItem);
  }

  return (
    <div className="form-group row">
      <label htmlFor={LABELS['lblCustomAgg']} className="col-sm-2 col-form-label"
             style={MARGIN_TEXT}> {LABELS['lblCustomAgg']}</label>
      <div className="form-group col-sm-7">
        <div className="form-group row"
             style={{paddingLeft: "15px", paddingRight: "15px"}}>
          <label htmlFor={LABELS['lblCustomAgg']}
                 className="col-form-label"> {LABELS['lblAggList']} </label>
          <select className="form-control" id={LABELS['lblCustomAgg']} size="5"
                  value={aggListVal} onChange={handleAggListChange}>
            {
              aggregations.map((item) =>
                <option key={item['agg_mapping'] + " - " + item['agg_value']}
                        value={item['agg_mapping'] + " - " + item['agg_value']}>
                  {item['agg_mapping'] + " - " + item['agg_value']}</option>)
            }
          </select>
        </div>
        <div className="form-group row">
          <div className="col-sm-4">
            <label htmlFor={LABELS['lblAggMapping']}
                   className="col-form-label"> {LABELS['lblAggMapping']} </label>
          </div>
          <div className="col-sm-8">
            <select className="form-control" id={LABELS['lblAggMapping']} value={aggMapping}
                    onChange={e => setAggMapping(e.target.value)}>
              {
                mappingList.map((item) =>
                  <option key={item} value={item} >{item}</option>)
              }
            </select>
          </div>
        </div>
        <div className="form-group row">
          <div className="col-sm-4">
            <label htmlFor={LABELS['lblAggValue']}
                   className="col-form-label"> {LABELS['lblAggValue']} </label>
          </div>
          <div className="col-sm-8">
            <input type="text" id={LABELS['lblAggValue']} className="form-control"
                   value={aggValue}
                   onChange={e => setAggValue(e.target.value)}/>
          </div>
        </div>
        <div className="form-group row">
          <div className="col-sm-12">
            <button type="button" style={{marginLeft: "3px"}}
                    className="btn btn-primary pull-right"
                    onClick={handleAddAggList}>{LABELS['lblAdd']}</button>
            <button type="button" className="btn btn-primary pull-right"
                    onClick={handleDeleteAggList}>{LABELS['lblDelete']}</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function FacetSearchDetailsLayout(
  {
    name_en, name_jp, mapping, active, aggregations
  }
) {

  function confirmRemoveFacet() {
    $("#facet_search_comfirm_modal").modal("show");
  }

  return (
    <div>
      <HeaderComponent/>
      <div className="row">
        <table class="table table-hover table-bordered searchable">
          <colgroup><col class="width_250px"/></colgroup>
          <tbody>
          <tr>
            <td><b>{LABELS['lblNameEN']}</b></td>
            <td>{name_en}</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblNameJP']}</b></td>
            <td>{name_jp}</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblMapping']}</b></td>
            <td>{mapping}</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblCustomAgg']}</b></td>
            <td>{
              aggregations.map(item =>
                <p>{item['agg_mapping'] + " - " + item['agg_value']}</p>)
            }</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblActive']}</b></td>
            <td>{active ? LABELS['lblDisplay'] : LABELS['lblHide']}</td>
          </tr>
          </tbody>
        </table>
        {LABELS['lblTypeScreen'] === 'delete' &&
          <div className="col-sm-7">
            <button type="button" style={{marginRight: "3px"}}
                    className="btn btn-primary"
                    onClick={confirmRemoveFacet}>{LABELS['lblDelete']}
            </button>
            <a href="/admin/facetsearch/" className="btn btn-danger"
               role="button">{LABELS['lblCancel']}</a>
          </div>
        }
      </div>
    </div>
  )
}

function HeaderComponent() {
  const hide = {
    list: '',
    new: '',
    edit: LABELS['lblTypeScreen'] === 'new' ? ' hide' : '',
    detail: LABELS['lblTypeScreen'] === 'new' ? ' hide' : '',
    delete: LABELS['lblTypeScreen'] === 'new' ? ' hide' : '',
  };
  const active = {
    list: LABELS['lblTypeScreen'] === '' ? 'active' : '',
    new: LABELS['lblTypeScreen'] === 'new' ? 'active' : '',
    edit: LABELS['lblTypeScreen'] === 'edit' ? 'active' : '',
    detail: LABELS['lblTypeScreen'] === 'detail' ? 'active' : '',
    delete: LABELS['lblTypeScreen'] === 'delete' ? 'active' : ''
  };
  const href = {
    list: '/admin/facetsearch/',
    new: '/admin/facetsearch/new/',
    edit: '/admin/facetsearch/edit/' + LABELS['lblFacetSearchId'],
    detail: '/admin/facetsearch/detail/' + LABELS['lblFacetSearchId'],
    delete: '/admin/facetsearch/delete/' + LABELS['lblFacetSearchId']
  };
  return (
    <div className="resource row">
      <ul class="nav nav-tabs">
        <li className={active.list + hide.list}><a href={href.list}>{LABELS['lblList']}</a></li>
        <li className={active.new + hide.new}><a href={href.new}>{LABELS['lblCreate']}</a></li>
        <li className={active.edit + hide.edit}><a href={href.edit}>{LABELS['lblEdit']}</a></li>
        <li className={active.detail + hide.detail}><a href={href.detail}>{LABELS['lblDetail']}</a></li>
        <li className={active.delete + hide.delete}><a href={href.delete}>{LABELS['lblDelete']}</a></li>
      </ul>
    </div>
  )
}

$("#Confirm_delete_button").click(function () {
  let data = {id: LABELS['lblFacetSearchId']}
  $.ajax({
    url: '/api/admin/facetsearch/remove',
    method: 'POST',
    contentType: 'application/json',
    dataType: 'json',
    data: JSON.stringify(data),
    success: function (response) {
      window.location.href = urlList;
    },
    error: function (error) {
      console.log(error);
    }
  });
});

const {useState, useEffect} = React;
const LABELS = {};
const urlList = window.location.origin + "/admin/facet-search/";

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
    $('#Confirm_delete_button').click(function () {
      handleRemoveFacet();
    });
    return <FacetSearchDetailsLayout {...JSON.parse(initValue)} />;
  }
}

function FacetSearchLayout(
  {
    name_en, name_jp, mapping, active, ui_type, is_open, display_number, search_condition, aggregations, mapping_list, detail_condition
  }
) {
  const [_nameEN, _setNameEN] = useState(name_en);
  const [_nameJP, _setNameJP] = useState(name_jp);
  const [_mapping, _setMapping] = useState(mapping);
  const [_active, _setActive] = useState(active);
  const [_uiType, _setUiType] = useState(ui_type);
  const [_isOpen, _setIsOpen] = useState(is_open);
  const [_displayNumber, _setDisplayNumber] = useState(display_number);
  const [_searchCondition, _setSearchCondition] = useState(search_condition);
  const [_aggregations, _setAggregations] = useState(aggregations);

  function handleSaveFacetSearch() {
    const URL = "/api/admin/facet-search/save";
    let errorMessage = "";
    if  ( (_nameEN === "") || (_nameJP === "") || (_mapping === "")  ){
      errorMessage = (LABELS['lblMsgRequired']);
     }else if ( _uiType === 'CheckboxList' && !_displayNumber ) {
        //If a checkbox UI is set and displayNumber is not entered, make an error.
        errorMessage = (LABELS['lblDisplayNumberValidation2']);
    } else if ( _displayNumber &&
       ( !Number.isInteger(Number(_displayNumber)) || _displayNumber < 1 || _displayNumber > 99 ) ) {
      //The displayNumber must be set to an integer value between 1 and 99.
      errorMessage = (LABELS['lblDisplayNumberValidation1']);
    } else {
      //It is an error if the parameter name for faceted search overlaps with the parameter name used for detail search.
      detail_condition.map((item) => {
        if(item[1] === 'range' || item[1] === 'dateRange'){
          //If the type is [range] or [dateRange], [_from] and [_to] are added to the parameter name.
          if(item[0] + '_from' === _nameEN || item[0] + '_to' === _nameEN){
            errorMessage = (LABELS['lblNameENValidation']);
          }
        } else if(item[1] === 'geo_distance') {
          //If the type is [geo_distance], [_lat], [_lon] and [_distance] are added to the parameter names.
          if(item[0] + '_lat' === _nameEN || item[0] + '_lon' === _nameEN || item[0] + '_distance' === _nameEN){
            errorMessage = (LABELS['lblNameENValidation']);
          }
        } else if(item[0] === _nameEN) {
          errorMessage = (LABELS['lblNameENValidation']);
        }
      });
    }

    if (errorMessage){
      showErrorMessage(errorMessage);
      return ;
    }

    let data = {
      name_en: _nameEN,
      name_jp: _nameJP,
      mapping: _mapping,
      active: _active,
      ui_type: _uiType,
      is_open: _isOpen,
      display_number: _displayNumber,
      search_condition: _searchCondition,
      aggregations: _aggregations,
      id:LABELS['lblFacetSearchId']
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
          window.location.href = urlList;
        } else {
          showErrorMessage(result.msg);
        }
      },
      error: function (error) {
        showErrorMessage(error);
      }
    });
  }

  /**
   * Returns whether or not RangeSlider is disabled for the specified UI type.
   * 
   * @param {string} value UI Type
   * @returns True if the UI type does not allow RangeSlider selection; false otherwise.
   */
    function isDisableRangeUi(value) {
      return value!=="temporal";
    }

  /**
   * Returns whether or not the UI type allows displayNumber to be entered.
   * @param {string} value UI Type
   * @returns True if the UI type does not allow displayNumber input; false otherwise.
   */
  function isDisableDisplayNumber(value) {
    return value!=="CheckboxList";
  }

  function isRangeSlider(ui_type) {
    return ui_type==='RangeSlider';
  }

  /**
   * Called when Mapping is changed to control whether or not RangeSlider input is allowed.
   */
  function handleChangeMapping(event) {
    _setMapping(event.target.value);
    handleUiTypeRange(event.target.value);
  }

  /**
   * Controls the UI type when Mapping is changed.
   * If the facet item has RangeSlider selected as the UI type and
   * is changed to a mapping that does not allow RangeSlider to be selected,
   * the UI type is forcibly changed to CheckboxList.
   * 
   * @param {string} value Value of selected Mapping.
   */
  function handleUiTypeRange(value) {
    let isDisable = isDisableRangeUi(value);
    if(isDisable && isRangeSlider(_uiType)) {
      _setUiType("CheckboxList");
    }
    $("#uiType_Range").prop("disabled",isDisable);
  }

  /**
   * Called when the UI type is changed.
   * The input state of displayNumber is controlled by the value of the selected UI type.
   */
  function handleChangeUiType(event) {
    _setUiType(event.target.value);
    let isDisable = isDisableDisplayNumber(event.target.value);
    if(isDisable){
      _setDisplayNumber(null);
    }
    $("#" + LABELS['lblDisplayNumber']).prop("disabled",isDisable);

    let isSlider = isRangeSlider(event.target.value);
    if(isSlider) {
      _setSearchCondition("AND");
      
    }
    $("#searchConditionOR").prop("disabled",isSlider);
  }

  return (
    <div>
      <HeaderComponent/>
      <br/>
      <div className="row">
        <InputTextComponent value={_nameEN} setValue={_setNameEN}
                            idName={LABELS['lblNameEN']} isRequired={true} isDisalbed={false} />
      </div>
      <div className="row">
        <InputTextComponent value={_nameJP} setValue={_setNameJP}
                            idName={LABELS['lblNameJP']} isRequired={true} isDisalbed={false}/>
      </div>
      <div className="row">
        <div className="form-group row">
          <label htmlFor={LABELS['lblMapping']}
          className="control-label col-xs-2 text-right field-required">
            {LABELS['lblMapping']}
          </label>
          <div className="controls col-xs-6">
            <select className="form-control" id={LABELS['lblMapping']}
                    value={_mapping}
                    onChange={handleChangeMapping}>
              {
                mapping_list.map((item) =>
                  <option value={item}>{item}</option>)
              }
            </select>
          </div>
        </div>
      </div>
      <div className="row">
        <div className="form-group row">
          <label htmlFor={LABELS['lblUiType']}
          className="control-label col-xs-2 text-right field-required">
            {LABELS['lblUiType']}
          </label>
          <div className="controls col-xs-6">
            <select className="form-control" id={LABELS['lblUiType']}
                    value={_uiType}
                    onChange={handleChangeUiType}>
              <option id='uiType_Checkbox' value="CheckboxList">CheckboxList</option>
              <option id='uiType_Select' value="SelectBox">SelectBox</option>
              {isDisableRangeUi(_mapping) && 
                <option id='uiType_Range' value="RangeSlider" disabled>RangeSlider</option>}
              {!isDisableRangeUi(_mapping) &&
                <option id='uiType_Range' value="RangeSlider">RangeSlider</option>}
            </select>
          </div>
        </div>
      </div>
      <div className="row">
        <InputTextComponent value={_displayNumber} setValue={_setDisplayNumber}
                            idName={LABELS['lblDisplayNumber']} isRequired={false}
                            isDisabled={isDisableDisplayNumber(_uiType)} />
      </div>
      <div className="row">
        <CustomAggregations aggregations={_aggregations}
                            setAggregations={_setAggregations}
                            mappingList={mapping_list}/>
      </div>
      <div className="row">
        <InputSearchConditionComponent value={_searchCondition} setValue={_setSearchCondition}
                              idName={LABELS['lblSearchCondition']} isSlider={isRangeSlider(_uiType)} />
      </div>
      <div className="row">
        <InputRadioComponent value={_active} setValue={_setActive}
                              idName={LABELS['lblActive']}/>
      </div>
      <div className="row">
        <InputOpenCloseComponent value={_isOpen} setValue={_setIsOpen}
                              idName={LABELS['lblOpenClose']}/>
      </div>
      <br/>
      <div className="row">
          <div className="form-group row">
            <div className="col-xs-offset-2 col-xs-5">
              <button type="button"
                      className="btn btn-primary save-button"
                      onClick={handleSaveFacetSearch}>
                        <span className="glyphicon glyphicon-download-alt" aria-hidden="true"/>
                        &nbsp;{LABELS['lblSave']}
                </button>
              <a href="/admin/facet-search/" className="btn btn-info cancel-button"
                style={{marginLeft: "10px", paddingTop:"10px"}}
                role="button">
                  <span className="glyphicon glyphicon-remove" aria-hidden="true"/>
                  &nbsp;{LABELS['lblCancel']}
              </a>
            </div>
          </div>
      </div>
    </div>
  )
}

function InputTextComponent({value, setValue, idName, isRequired ,isDisabled}) {

  function handleChange(event) {
    event.preventDefault();
    let target = event.target;
    setValue(target.value);
  }

  return (
    <div>
      <div className="form-group row">
        <label htmlFor={idName}
          className={"control-label col-xs-2 text-right" + (isRequired ? "field-required" : "")}>
          {idName}
        </label>
        <div className="controls col-xs-6">
          {isDisabled && <input type="text" id={idName} className="form-control" value={value} onChange={handleChange} disabled/>}
          {!isDisabled && <input type="text" id={idName} className="form-control" value={value} onChange={handleChange}/>}
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
      <label htmlFor={idName} className="control-label col-xs-2 text-right">
        {idName}
      </label>
      <div className="controls col-xs-6">
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

function InputOpenCloseComponent({value, setValue, idName}) {

  function handleChangeDisplay(event) {
    setValue(!value);
  }

  return (
    <div className="form-group">
      <label htmlFor={idName} className="control-label col-xs-2 text-right">
        {idName}
      </label>
      <div className="controls col-xs-6">
        <label className="radio-inline" htmlFor="openCloseOpen">
          <input type="radio" id="openCloseOpen" checked={value === true}
                 onChange={handleChangeDisplay}/>
          {LABELS['lblOpenCloseOpen']}
        </label>
        <label className="radio-inline" htmlFor="openCloseClose">
          <input type="radio" id="openCloseClose" checked={value === false}
                 onChange={handleChangeDisplay}/>
          {LABELS['lblOpenCloseClose']}
        </label>
      </div>
    </div>
  )
}

function InputSearchConditionComponent({value, setValue, idName, isSlider}) {

  function handleChangeDisplay(event) {
    setValue(event.target.value);
  }

  return (
    <div className="form-group">
      <label htmlFor={idName} className="control-label col-xs-2 text-right">
        {idName}
      </label>
      <div className="controls col-xs-6">
        <label className="radio-inline" htmlFor="searchConditionOR">
          {isSlider && <input type="radio" id="searchConditionOR" checked={value === "OR"} value="OR"
                 onChange={handleChangeDisplay} disabled/>}
          {!isSlider && <input type="radio" id="searchConditionOR" checked={value === "OR"} value="OR"
                 onChange={handleChangeDisplay} />}
          {LABELS['lblSearchConditionOR']}
        </label>
        <label className="radio-inline" htmlFor="searchConditionAND">
          <input type="radio" id="searchConditionAND" checked={value === "AND"} value="AND"
                 onChange={handleChangeDisplay}/>
          {LABELS['lblSearchConditionAND']}
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
    if (!aggMapping) {
      alert(LABELS['lblMsgAggMapping']);
      return;
    } else if (isExist) {
      alert(LABELS['lblMsgExist']);
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
      <label htmlFor={LABELS['lblCustomAgg']}
        className="control-label col-xs-2 text-right">
         {LABELS['lblCustomAgg']}
      </label>
      <div className="form-group col-sm-6">
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
    name_en, name_jp, mapping, active, ui_type, is_open, display_number, search_condition, aggregations
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
          <colgroup><col class="width_300px"/></colgroup>
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
            <td><b>{LABELS['lblUiType']}</b></td>
            <td>{ui_type}</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblDisplayNumber']}</b></td>
            <td>{display_number}</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblCustomAgg']}</b></td>
            <td>{
              aggregations.map(item =>
                <p>{item['agg_mapping'] + " - " + item['agg_value']}</p>)
            }</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblSearchCondition']}</b></td>
            <td>{search_condition}</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblActive']}</b></td>
            <td>{active ? LABELS['lblDisplay'] : LABELS['lblHide']}</td>
          </tr>
          <tr>
            <td><b>{LABELS['lblOpenClose']}</b></td>
            <td>{is_open ? LABELS['lblOpenCloseOpen'] : LABELS['lblOpenCloseClose']}</td>
          </tr>
          </tbody>
        </table>

        {!check_type() && (
        <div className="form-group row">
          <div className="col-xs-offset-2 col-xs-5">
            <button type="button" style={{marginLeft: "10px"}}
                    className="btn btn-danger delete-button"
                    onClick={confirmRemoveFacet}>
                      <span className="glyphicon glyphicon-trash" aria-hidden="true"/>
                      &nbsp;{LABELS['lblDelete']}
            </button>
            <a href="/admin/facet-search/"
              className="btn btn-info cancel-button"
              style={{marginLeft: "10px", paddingTop:"10px"}}
              role="button">
                <span className="glyphicon glyphicon-remove" aria-hidden="true"/>
                {LABELS['lblCancel']}
            </a>
          </div>
        </div>
        )}
      </div>
    </div>
  )
}

function HeaderComponent() {
  const hideTab = LABELS['lblTypeScreen'] === 'new' ? ' hide' : '';
  const active = {
    list: LABELS['lblTypeScreen'] === '' ? 'active' : '',
    new: LABELS['lblTypeScreen'] === 'new' ? 'active' : '',
    edit: LABELS['lblTypeScreen'] === 'edit' ? 'active' : '',
    detail: LABELS['lblTypeScreen'] === 'details' ? 'active' : '',
    delete: LABELS['lblTypeScreen'] === 'delete' ? 'active' : ''
  }
  const href = {
    list: '/admin/facet-search/',
    new: '/admin/facet-search/new/',
    edit: '/admin/facet-search/edit/' + LABELS['lblFacetSearchId'],
    detail: '/admin/facet-search/details/' + LABELS['lblFacetSearchId'],
    delete: '/admin/facet-search/delete/' + LABELS['lblFacetSearchId']
  }
  return (
    <div className="resource row">
      <ul class="nav nav-tabs">
        <li className={active.list}><a href={href.list}>{LABELS['lblList']}</a></li>
        <li className={active.new}><a href={href.new} >{LABELS['lblCreate']}</a></li>
        <li className={active.edit + hideTab}><a href={href.edit} >{LABELS['lblEdit']}</a></li>
        <li className={active.detail + hideTab}><a href={href.detail} >{LABELS['lblDetail']}</a></li>
        <li className={active.delete + hideTab}><a href={href.delete} >{LABELS['lblDelete']}</a></li>
      </ul>
    </div>
  )
}

function handleRemoveFacet() {
  let data = {id: LABELS['lblFacetSearchId']}
  $("#facet_search_comfirm_modal").modal("hide")
  $.ajax({
    url: '/api/admin/facet-search/remove',
    method: 'POST',
    contentType: 'application/json',
    dataType: 'json',
    data: JSON.stringify(data),
    success: function (result) {
      if (result.status) {
        console.log(result.msg, 2);
        window.location.href = urlList;
      } else {
        showErrorMessage(result.msg);
      }
    },
    error: function (error) {
      showErrorMessage(error);
    }
  });
}

function showErrorMessage(errorMessage) {
  $("#inputModal").html(errorMessage);
  $("#allModal").modal("show");
}

function check_type() {
  return LABELS['lblTypeScreen'] === 'details';
}

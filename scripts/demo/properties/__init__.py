from . import (access_right, access, advisor, alternative_title, annual_report, apc, application_date, approval_date, author_name, biblio_info, collection_method, conference, contributor, corresponding_output_id, corresponding_usage_application_id, creator, data_type, dataset_usage, date_granted, date, degree_grantor, degree_name, description, dissertation_number, distributor, end_page, file_price, files, full_name, funding_reference, geocover, geolocation, guarantor, heading, identifier_registration, identifier, issue, item_title, language, link, number_of_pages, output_type, other_language, published_date, published_doi_url, published_media_name, publisher, related_publications, related_study, relation, research_plan, research_title, resource_type_simple, resource_type, rights_holder, rights, S_file, S_identifier, sampling, series, source_id, source_title, start_page, stop_continue, study_id, subject, summary, temporal, text, textarea, thumbnail, time_period, title, topic, unit_of_analysis, universe, uri, usage_report_id, user_information, version_type, version, volume, wf_issued_date)

class AddProperty():
    def __init__(self, add_func, title, title_ja='', title_en='',
                 required=False, multiple=False, showlist=False,
                 newline=False, hide=False, displayoneline= False,
                 mapping=True):
        self.add_func = add_func
        self.property_title = title
        self.property_title_ja = title_ja
        self.property_title_en = title_en
        self.option = {
            "crtf": newline,
            "hidden": hide,
            "oneline": displayoneline,
            "multiple": multiple,
            "required": required,
            "showlist": showlist
        }
        self.mapping = mapping

    access_right = access_right.add
    access = access.add
    advisor = advisor.add
    alternative_title = alternative_title.add
    annual_report = annual_report.add
    apc = apc.add
    application_date = application_date.add
    approval_date = approval_date.add
    author_name = author_name.add
    biblio_info = biblio_info.add
    collection_method = collection_method.add
    conference = conference.add
    contributor = contributor.add
    corresponding_output_id = corresponding_output_id.add
    corresponding_usage_application_id = corresponding_usage_application_id.add
    creator = creator.add
    data_type = data_type.add
    dataset_usage = dataset_usage.add
    date_granted = date_granted.add
    date = date.add
    degree_grantor = degree_grantor.add
    degree_name = degree_name.add
    description = description.add
    dissertation_number = dissertation_number.add
    distributor = distributor.add
    end_page = end_page.add
    file_price = file_price.add
    files = files.add
    full_name = full_name.add
    funding_reference = funding_reference.add
    geocover = geocover.add
    geolocation = geolocation.add
    guarantor = guarantor.add
    heading = heading.add
    identifier_registration = identifier_registration.add
    identifier = identifier.add
    issue = issue.add
    item_title = item_title.add
    language = language.add
    link = link.add
    number_of_pages = number_of_pages.add
    output_type = output_type.add
    other_language = other_language.add
    published_date = published_date.add
    published_doi_url = published_doi_url.add
    published_media_name = published_media_name.add
    publisher = publisher.add
    related_publications = related_publications.add
    related_study = related_study.add
    relation = relation.add
    research_plan = research_plan.add
    research_title = research_title.add
    resource_type_simple = resource_type_simple.add
    resource_type = resource_type.add
    rights_holder = rights_holder.add
    rights = rights.add
    S_file = S_file.add
    S_identifier = S_identifier.add
    sampling = sampling.add
    series = series.add
    source_id = source_id.add
    source_title = source_title.add
    start_page = start_page.add
    stop_continue = stop_continue.add
    study_id = study_id.add
    subject = subject.add
    summary = summary.add
    temporal = temporal.add
    text = text.add
    textarea = textarea.add
    thumbnail = thumbnail.add
    time_period = time_period.add
    title = title.add
    topic = topic.add
    unit_of_analysis = unit_of_analysis.add
    universe = universe.add
    uri = uri.add
    usage_report_id = usage_report_id.add
    user_information = user_information.add
    version_type = version_type.add
    version = version.add
    volume = volume.add
    wf_issued_date = wf_issued_date.add
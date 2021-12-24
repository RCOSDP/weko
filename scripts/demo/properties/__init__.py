from . import (access_right, access, advisor, alternative_title, annual_report, apc, application_date, approval_date, author_name, biblio_info, collection_method, conference, contributor, corresponding_output_id, corresponding_usage_application_id, creator, data_type, dataset_usage, date_granted, date, degree_grantor, degree_name, description, dissertation_number, distributor, end_page, file_price, files, full_name, funding_reference, geocover, geolocation, guarantor, heading, identifier_registration, identifier, issue, item_title, language, link, number_of_pages, output_type, other_language, published_date, published_doi_url, published_media_name, publisher, record_name, related_publications, related_study, relation, research_plan, research_title, resource_type_simple, resource_type, rights_holder, rights, S_file, S_identifier, sampling, series, source_id, source_title, start_page, stop_continue, study_id, subject, summary, temporal, text, textarea, thumbnail, time_period, title, topic, unit_of_analysis, universe, uri, usage_report_id, user_information, version_type, version, volume, wf_issued_date)


class AddProperty():
    def __init__(self, add_func, title, title_ja='', title_en='',
                 required=False, multiple=False, showlist=False,
                 newline=False, hide=False, displayoneline= False):
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

    @classmethod
    def access_right(self):
        return access_right.add

    @classmethod
    def access(self):
        return access.add

    @classmethod
    def advisor(self):
        return advisor.add

    @classmethod
    def alternative_title(self):
        return alternative_title.add

    @classmethod
    def annual_report(self):
        return annual_report.add

    @classmethod
    def apc(self):
        return apc.add

    @classmethod
    def application_date(self):
        return application_date.add

    @classmethod
    def approval_date(self):
        return approval_date.add

    @classmethod
    def author_name(self):
        return author_name.add

    @classmethod
    def biblio_info(self):
        return biblio_info.add

    @classmethod
    def collection_method(self):
        return collection_method.add

    @classmethod
    def conference(self):
        return conference.add

    @classmethod
    def contributor(self):
        return contributor.add

    @classmethod
    def corresponding_output_id(self):
        return corresponding_output_id.add

    @classmethod
    def corresponding_usage_application_id(self):
        return corresponding_usage_application_id.add

    @classmethod
    def creator(self):
        return creator.add

    @classmethod
    def data_type(self):
        return data_type.add

    @classmethod
    def dataset_usage(self):
        return dataset_usage.add

    @classmethod
    def date_granted(self):
        return date_granted.add

    @classmethod
    def date(self):
        return date.add

    @classmethod
    def degree_grantor(self):
        return degree_grantor.add

    @classmethod
    def degree_name(self):
        return degree_name.add

    @classmethod
    def description(self):
        return description.add

    @classmethod
    def dissertation_number(self):
        return dissertation_number.add

    @classmethod
    def distributor(self):
        return distributor.add

    @classmethod
    def end_page(self):
        return end_page.add

    @classmethod
    def file_price(self):
        return file_price.add

    @classmethod
    def files(self):
        return files.add

    @classmethod
    def full_name(self):
        return full_name.add

    @classmethod
    def funding_reference(self):
        return funding_reference.add

    @classmethod
    def geocover(self):
        return geocover.add

    @classmethod
    def geolocation(self):
        return geolocation.add

    @classmethod
    def guarantor(self):
        return guarantor.add

    @classmethod
    def heading(self):
        return heading.add

    @classmethod
    def identifier_registration(self):
        return identifier_registration.add

    @classmethod
    def identifier(self):
        return identifier.add

    @classmethod
    def issue(self):
        return issue.add

    @classmethod
    def item_title(self):
        return item_title.add

    @classmethod
    def language(self):
        return language.add

    @classmethod
    def link(self):
        return link.add

    @classmethod
    def number_of_pages(self):
        return number_of_pages.add

    @classmethod
    def output_type(self):
        return output_type.add

    @classmethod
    def other_language(self):
        return other_language.add

    @classmethod
    def published_date(self):
        return published_date.add

    @classmethod
    def published_doi_url(self):
        return published_doi_url.add

    @classmethod
    def published_media_name(self):
        return published_media_name.add

    @classmethod
    def publisher(self):
        return publisher.add

    @classmethod
    def record_name(self):
        return record_name.add

    @classmethod
    def related_publications(self):
        return related_publications.add

    @classmethod
    def related_study(self):
        return related_study.add

    @classmethod
    def relation(self):
        return relation.add

    @classmethod
    def research_plan(self):
        return research_plan.add

    @classmethod
    def research_title(self):
        return research_title.add

    @classmethod
    def resource_type_simple(self):
        return resource_type_simple.add

    @classmethod
    def resource_type(self):
        return resource_type.add

    @classmethod
    def rights_holder(self):
        return rights_holder.add

    @classmethod
    def rights(self):
        return rights.add

    @classmethod
    def S_file(self):
        return S_file.add

    @classmethod
    def S_identifier(self):
        return S_identifier.add

    @classmethod
    def sampling(self):
        return sampling.add

    @classmethod
    def series(self):
        return series.add

    @classmethod
    def source_id(self):
        return source_id.add

    @classmethod
    def source_title(self):
        return source_title.add

    @classmethod
    def start_page(self):
        return start_page.add

    @classmethod
    def stop_continue(self):
        return stop_continue.add
    
    @classmethod
    def study_id(self):
        return study_id.add

    @classmethod
    def subject(self):
        return subject.add

    @classmethod
    def summary(self):
        return summary.add

    @classmethod
    def temporal(self):
        return temporal.add

    @classmethod
    def text(self):
        return text.add

    @classmethod
    def textarea(self):
        return textarea.add

    @classmethod
    def thumbnail(self):
        return thumbnail.add

    @classmethod
    def time_period(self):
        return time_period.add

    @classmethod
    def title(self):
        return title.add

    @classmethod
    def topic(self):
        return topic.add

    @classmethod
    def unit_of_analysis(self):
        return unit_of_analysis.add

    @classmethod
    def universe(self):
        return universe.add

    @classmethod
    def uri(self):
        return uri.add

    @classmethod
    def usage_report_id(self):
        return usage_report_id.add

    @classmethod
    def user_information(self):
        return user_information.add

    @classmethod
    def version_type(self):
        return version_type.add

    @classmethod
    def version(self):
        return version.add

    @classmethod
    def volume(self):
        return volume.add

    @classmethod
    def wf_issued_date(self):
        return wf_issued_date.add
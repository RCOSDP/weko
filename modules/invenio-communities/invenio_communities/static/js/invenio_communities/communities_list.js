function printCatalogInfo(data) {
  if (data == "None" || data == "[]") {
    console.log("data is null");
    return;
  }
  console.log(data);

  string_contributors = ""
  string_subjects = ""
  const cleanedString = data.replaceAll("&#39;", "\"");
  jsonString = "\{\"catalog\":" + cleanedString + "\}";
  const json = JSON.parse(jsonString);

  console.log(json.catalog);
  json.catalog.forEach(item => {
    if ("catalog_subjects" in item) {
      item.catalog_subjects.forEach(subject => {
        string_subjects = subject.catalog_subject + ", ";
        string_subjects += subject.catalog_subject_uri + ", ";
        string_subjects += subject.catalog_subject_scheme + ", ";
        string_subjects += subject.catalog_subject_language;
      });
      document.write("<p>" + string_subjects + "</p>");
    }
    if ("catalog_contributors" in item) {
      item.catalog_contributors.forEach(contributor => {
        if ("contributor_type" in contributor) {
          string_contributors = contributor.contributor_type;
        }
        if ("contributor_names" in contributor) {
          contributor.contributor_names.forEach(name => {
            if ("contributor_name" in name) {
              string_contributors += ", " + name.contributor_name;
            }
            if ("contributor_name_language" in name) {
              string_contributors += ", " + name.contributor_name_language;
            }
          });
        }
        document.write("<p>" + string_contributors + "</p>");
      });
    }
  });
}

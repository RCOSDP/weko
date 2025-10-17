export default function (obj: any, id: string) {
  let result: any = {};
  obj['@graph'].forEach((element: any) => {
    if (element['@id'] === id) {
      result = element;
    }
  });
  return result;
}

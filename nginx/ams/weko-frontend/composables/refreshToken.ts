export default function () {
  const expires = Number(localStorage.getItem('token:expires'));
  const issue = Number(localStorage.getItem('token:issue')) ?? 0;

  if (expires) {
    if (
      issue + expires * 1000 >= Date.now() &&
      issue + (expires - useRuntimeConfig().public.tokenRefreshLimit) * 1000 <= Date.now()
    ) {
      useFetch('/api/token/refresh?refreshToken=' + String(localStorage.getItem('token:refresh')))
        .then((response) => {
          // @ts-ignore
          localStorage.setItem('token:type', response.data.value.tokenType);
          // @ts-ignore
          localStorage.setItem('token:access', response.data.value.accessToken);
          // @ts-ignore
          localStorage.setItem('token:refresh', response.data.value.refreshToken);
          // @ts-ignore
          localStorage.setItem('token:expires', response.data.value.expires);
          localStorage.setItem('token:issue', String(Date.now()));
        })
        .catch((error) => {
          console.log(error);
        })
        .finally(() => {});
    }
  }
}

export default function () {
  const expires = Number(localStorage.getItem('token:expires'));
  const issue = Number(localStorage.getItem('token:issue')) ?? 0;

  if (expires) {
    if (
      issue + expires * 1000 >= Date.now() &&
      issue + (expires - useRuntimeConfig().public.tokenRefreshLimit) * 1000 <= Date.now()
    ) {
      useFetch('/api/token/refresh', {
        method: 'GET',
        params: { refreshToken: String(localStorage.getItem('token:refresh')) }
      }).then((response) => {
        if (response.status.value === 'success') {
          const data: any = response.data.value;
          localStorage.setItem('token:type', data.tokenType);
          localStorage.setItem('token:access', data.accessToken);
          localStorage.setItem('token:refresh', data.refreshToken);
          localStorage.setItem('token:expires', data.expires);
          localStorage.setItem('token:issue', String(Date.now()));
        }
      });
    }
  }
}

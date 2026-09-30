export default defineEventHandler(async (event) => {
  // process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // NOTE: オレオレ証明書を使用している場合は有効にする

  return await new Promise((resolve, reject) => {
    let tokenType = '';
    let accessToken = '';
    let refreshToken = '';
    let expires = 0;

    const formData = new FormData();
    formData.append('client_id', useRuntimeConfig().public.clientId);
    formData.append('client_secret', useRuntimeConfig().clientSecret);
    formData.append('grant_type', 'authorization_code');
    formData.append('code', String(getQuery(event).code));
    formData.append('redirect_uri', useRuntimeConfig().public.redirectURI);

    $fetch(useAppConfig().wekoOrigin + '/oauth/token', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'POST',
      body: formData,
      onResponse({ response }) {
        if (response.status === 200) {
          tokenType = response._data.token_type;
          accessToken = response._data.access_token;
          refreshToken = response._data.refresh_token;
          expires = response._data.expires_in;
        }
        resolve({ tokenType, accessToken, refreshToken, expires });
      },
      onResponseError(context) {
        // pm2にログファイル出力
        console.log(context); // eslint-disable-line
        reject(new Error('Failed to create access token.'));
      }
    }).catch((error) => {
      // pm2にログファイル出力
      console.log(error); // eslint-disable-line
      reject(new Error('API execution failed.'));
    });
  });
});

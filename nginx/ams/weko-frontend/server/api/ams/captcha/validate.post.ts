export default defineEventHandler(async (event) => {
  // process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // NOTE: オレオレ証明書を使用している場合は有効にする

  const body: any = await readBody(event);
  const cacheControl = getHeader(event, 'Cache-Control');
  const pragma = getHeader(event, 'Pragma');
  const acceptLanguage = getHeader(event, 'accept-language');
  let authorizationToken = '';

  return await new Promise((resolve, reject) => {
    // 文字認証の照合
    $fetch(useAppConfig().wekoApi + '/captcha/validate', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'POST',
      headers: {
        'Cache-Control': cacheControl ?? 'no-store',
        Pragma: pragma ?? 'no-cache',
        'Accept-Language': acceptLanguage ?? 'ja'
      },
      body: {
        key: body.key,
        calculation_result: body.calculation_result
      },
      onResponse({ response }) {
        if (response.status === 200) {
          authorizationToken = response._data.authorization_token;
          resolve({ authorization_token: authorizationToken });
        } else if (response.status >= 400) {
          reject(
            createError({
              statusCode: response.status,
              statusMessage: response._data.message
            })
          );
        }
      },
      onResponseError(context) {
        if (context.response && context.response.status >= 500) {
          // pm2にログファイル出力
          console.log(context);
        }
        reject(new Error('API execution failed.'));
      }
    }).catch((error) => {
      if (error.response && error.response.status >= 500) {
        // pm2にログファイル出力
        console.log(error);
      }
      reject(new Error('API execution failed.'));
    });
  });
});

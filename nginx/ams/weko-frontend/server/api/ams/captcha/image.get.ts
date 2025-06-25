export default defineEventHandler(async (event) => {
  // process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // NOTE: オレオレ証明書を使用している場合は有効にする

  const cacheControl = getHeader(event, 'Cache-Control');
  const pragma = getHeader(event, 'Pragma');
  const acceptLanguage = getHeader(event, 'accept-language');
  let image = '';
  let key = '';
  let ttl = '';

  return await new Promise((resolve, reject) => {
    // 文字認証用の画像取得
    $fetch(useAppConfig().wekoApi + '/captcha/image', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'GET',
      headers: {
        'Cache-Control': cacheControl ?? 'no-store',
        Pragma: pragma ?? 'no-cache',
        'Accept-Language': acceptLanguage ?? 'ja'
      },
      onResponse({ response }) {
        if (response.status === 200) {
          image = response._data.image;
          key = response._data.key;
          ttl = response._data.ttl;
          resolve({ image, key, ttl });
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

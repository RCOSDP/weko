export default defineEventHandler(async (event) => {
  // process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // NOTE: オレオレ証明書を使用している場合は有効にする

  const params = event.context.params;
  if (!params || !params.id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request: Missing ID parameter'
    });
  }
  const { id: itemId } = params;
  const body: any = await readBody(event);
  const cacheControl = getHeader(event, 'Cache-Control');
  const pragma = getHeader(event, 'Pragma');
  const acceptLanguage = getHeader(event, 'accept-language');

  return await new Promise((resolve, reject) => {
    // リクエスト送信
    $fetch(useAppConfig().wekoApi + '/records/' + itemId + '/request-mail', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'POST',
      headers: {
        'Cache-Control': cacheControl ?? 'no-store',
        Pragma: pragma ?? 'no-cache',
        'Accept-Language': acceptLanguage ?? 'ja'
      },
      body: {
        from: body.from,
        subject: body.subject,
        message: body.message,
        key: body.key,
        authorization_token: body.authorization_token
      },
      onResponse({ response }) {
        if (response.status === 200) {
          resolve('');
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

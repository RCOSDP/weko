export default defineEventHandler(async (event) => {
  const code = String(getQuery(event).code ?? '');
  if (!code) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Missing authorization code.',
    });
  }

  const params = new URLSearchParams();
  params.append('client_id', useRuntimeConfig().public.clientId);
  params.append('client_secret', useRuntimeConfig().clientSecret);
  params.append('grant_type', 'authorization_code');
  params.append('code', code);
  params.append('redirect_uri', useRuntimeConfig().public.redirectURI);
  
  try {
    const response = await $fetch<{
      token_type: string;
      access_token: string;
      refresh_token: string;
      expires_in: number;
    }>(useAppConfig().wekoOrigin + '/oauth/token', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    return {
      tokenType: response.token_type ?? '',
      accessToken: response.access_token ?? '',
      refreshToken: response.refresh_token ?? '',
      expires: response.expires_in ?? 0,
    };
  } catch (error: any) {
    console.error('oauth/token error', {
      message: error?.message,
      cause: error?.cause,
      data: error?.data,
      response: error?.response,
    });

  throw createError({
    statusCode: error?.response?.status || 500,
    statusMessage: error?.data?.error || 'Failed to create access token.',
  });
  }
});
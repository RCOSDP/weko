import { createTransport } from 'nodemailer';

export default defineEventHandler(async (event) => {
  // process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // NOTE: オレオレ証明書を使用している場合は有効にする
  const body: any = await readBody(event);

  return await new Promise((resolve, reject) => {
    // 文字認証
    $fetch(useAppConfig().wekoApi + '/captcha/validate', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'POST',
      body: {
        key: body.key,
        calculation_result: body.answer
      },
      onResponse({ response }) {
        // 認証完了後メール送信
        if (response.status === 200) {
          const conf = useRuntimeConfig();
          let transporter;

          if (String(body.mailType) === 'gmail') {
            transporter = createTransport({
              service: 'Gmail',
              auth: {
                user: conf.contact.gmail.address,
                pass: conf.contact.gmail.pass
              }
            });
          } else {
            transporter = createTransport({
              host: conf.contact.smtp.host,
              port: Number(conf.contact.smtp.port),
              auth: {
                user: conf.contact.smtp.user,
                pass: conf.contact.smtp.pass
              }
            });
          }

          // NOTE: メール内容をテンプレート化したい場合はhtmlを送信する方法を考える
          transporter
            .sendMail({
              from: String(body.address),
              to: conf.contact.to,
              subject: conf.contact.subject + body.type,
              text:
                'Type: ' +
                String(body.type) +
                '\n' +
                'Name: ' +
                String(body.name) +
                '\n' +
                'Email: ' +
                String(body.address) +
                '\n\n' +
                String(body.contents)
            })
            .then(() => {
              resolve('Complete sending');
            })
            .catch((e) => {
              // pm2にログファイル出力
              console.log(e); // eslint-disable-line
              resolve('Failed sending');
            });
        }
      },
      onResponseError(context) {
        // pm2にログファイル出力
        console.log(context); // eslint-disable-line
        resolve('Failed certification');
      }
    }).catch((error) => {
      // pm2にログファイル出力
      console.log(error); // eslint-disable-line
      reject(new Error('API execution failed.'));
    });
  });
});

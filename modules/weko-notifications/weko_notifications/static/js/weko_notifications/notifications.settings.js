function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

async function getVapidPublicKey() {
  const response = await fetch('/inbox/subscription/vapid-public-key');
  const publicKey = await response.text();
  return publicKey;
}

async function subscribePush(reg) {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    alert('Push messaging is not supported in your browser.');
    return;
  }
  if (Notification.permission === 'default') {
    await Notification.requestPermission();
  }
  try {
    const publicKey = await getVapidPublicKey();
    const applicationServerKey = urlBase64ToUint8Array(publicKey);
    const subscription = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey
    });
    console.log('Push subscription:', subscription);
    console.log('Push subscription:', subscription.toJSON());
    return subscription.toJSON();
  } catch (e) {
    console.error(e);
  }
}

async function unsubscribePush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    alert('Push messaging is not supported in your browser.');
    return null;
  }
  try {
    const reg = await navigator.serviceWorker.getRegistration('/static/gen/');
    if (!reg) {
      console.error('Service worker registration not found.');
      return null;
    }
    const subscription = await reg.pushManager.getSubscription();
    if (subscription) {
      await subscription.unsubscribe();
      console.log('Push unsubscription:', subscription);
      return subscription.toJSON();
    } else {
      console.log('No subscription found.');
      return null;
    }
  } catch (e) {
    console.error(e);
    return null;
  }
}

async function registerServiceWorker() {
  try {
    const reg = await navigator.serviceWorker.register('/static/gen/sw.js', { scope: '/static/gen/' });
    reg.addEventListener('updatefound', () => {
      const newWorker = reg.installing;
      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          newWorker.postMessage({ action: 'skipWaiting' });
        }
      });
    });
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    });
    return reg;
  } catch (e) {
    console.error('Service worker registration failed:', e);
    return null;
  }
}

const handleFormSubmit = async (event) => {
  event.preventDefault();

  const checkbox = document.getElementById('notifications-subscribe_webpush');

  let subscription;
  if (checkbox.checked) {
    try {
      const reg = await registerServiceWorker();
      if (!reg || !reg.active) {
        console.error('Service worker registration failed.');
        return;
      }
      subscription = await subscribePush(reg);
    } catch (e) {
      console.error(e);
      return;
    }
  } else {
    subscription = await unsubscribePush();
  }

  document.getElementById('notifications-webpush_endpoint').value
    = subscription ? subscription.endpoint : null;
  document.getElementById('notifications-webpush_expiration_time').value
    = subscription ? subscription.expirationTime : null;
  document.getElementById('notifications-webpush_p256dh').value
    = subscription ? subscription.keys.p256dh : null;
  document.getElementById('notifications-webpush_auth').value
    = subscription ? subscription.keys.auth : null;

}

document.addEventListener('DOMContentLoaded', async () => {
  const checkbox = document.getElementById('notifications-subscribe_webpush');
  try {
    const reg = await navigator.serviceWorker.getRegistration('/static/gen/');
    if (reg) {
      const subscription = await reg.pushManager.getSubscription();
      checkbox.checked = !!subscription;
    } else {
      checkbox.checked = false;
    }
  } catch (e) {
    console.error(e);
    checkbox.checked = false;
  }

  const form = document.querySelector('form[name="notifications_form"]');
  form.addEventListener('submit', async (event) => {
    await handleFormSubmit(event);
    HTMLFormElement.prototype.submit.call(form);
  });
});

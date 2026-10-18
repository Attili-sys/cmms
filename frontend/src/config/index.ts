const getRuntimeValue = (
  key: string,
  defaultValue = ''
): string | undefined => {
  const envValue = process.env[`REACT_APP_${key}`];
  const runtimeValue = window.__RUNTIME_CONFIG__?.[key]?.trim();
  return envValue || runtimeValue || defaultValue;
};

export const googleMapsConfig = {
  apiKey: getRuntimeValue('GOOGLE_KEY')
};

export const normalizeApiUrl = (raw?: string): string => {
  if (!raw || !raw.trim()) {
    return '/api/';
  }
  const trimmed = raw.trim();
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed.endsWith('/') ? trimmed : `${trimmed}/`;
  }
  const withLeading = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  return withLeading.endsWith('/') ? withLeading : `${withLeading}/`;
};

const rawApiUrl = getRuntimeValue('API_URL');
export const apiUrl = normalizeApiUrl(rawApiUrl);

const rawHomeUrl = getRuntimeValue('HOME_URL');
export const homeUrl = rawHomeUrl
  ? rawHomeUrl.endsWith('/')
    ? rawHomeUrl
    : rawHomeUrl + '/'
  : 'http://localhost:4000/';

export const zendeskKey = '';

export const googleTrackingId = getRuntimeValue('GOOGLE_TRACKING_ID');
export const oauth2Provider = getRuntimeValue('OAUTH2_PROVIDER') as
  | 'GOOGLE'
  | 'MICROSOFT';

export const isEmailVerificationEnabled =
  getRuntimeValue('INVITATION_VIA_EMAIL') === 'true';

export const isCloudVersion = getRuntimeValue('CLOUD_VERSION') === 'true';
export const sourceCodeUrl = getRuntimeValue(
  'SOURCE_CODE_URL',
  'https://github.com/Attili-sys/cmms'
);

const apiHostName = new URL(apiUrl, window.location.origin).hostname;
export const IS_LOCALHOST =
  apiHostName === 'localhost' || apiHostName === '127.0.0.1';

export const isSSOEnabled = getRuntimeValue('ENABLE_SSO') === 'true';

export const customLogoPaths: { white?: string; dark: string } =
  getRuntimeValue('LOGO_PATHS')
    ? JSON.parse(getRuntimeValue('LOGO_PATHS'))
    : null;
type ThemeColors = {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  black: string;
  white: string;
  primaryAlt: string;
};

export const customColors: ThemeColors = getRuntimeValue('CUSTOM_COLORS')
  ? JSON.parse(getRuntimeValue('CUSTOM_COLORS'))
  : null;

export interface BrandRawConfig {
  name: string;
  shortName: string;
  website: string;
  mail: string;
  addressStreet: string;
  phone: string;
  addressCity: string;
}
export const brandRawConfig: BrandRawConfig = getRuntimeValue('BRAND_CONFIG')
  ? JSON.parse(getRuntimeValue('BRAND_CONFIG'))
  : null;

export const demoLink: string = getRuntimeValue('DEMO_LINK');

export const isWhiteLabeled: boolean = !!(customLogoPaths || brandRawConfig);

export const IS_ORIGINAL_CLOUD = !isWhiteLabeled && isCloudVersion;

export const recaptchaSiteKey = getRuntimeValue('RECAPTCHA_SITE_KEY');

export const intercomId = getRuntimeValue('INTERCOM_ID');
export const clarityId = getRuntimeValue('CLARITY_ID');
export const ldapEnabled = getRuntimeValue('LDAP_ENABLED') === 'true';

export const sentryDsn = getRuntimeValue('SENTRY_DSN');
export const sentryEnvironment = getRuntimeValue(
  'SENTRY_ENVIRONMENT',
  'production'
);
export const sentryRelease = getRuntimeValue(
  'SENTRY_RELEASE',
  'atlas-frontend'
);

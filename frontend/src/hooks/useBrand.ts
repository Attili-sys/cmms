import { BrandRawConfig, brandRawConfig } from '../config';

interface BrandConfig extends BrandRawConfig {
  logo: { white: string; dark: string };
}
export function useBrand(): BrandConfig {
  const defaultBrand: Omit<BrandConfig, 'logo'> = {
    name: 'Canvas',
    shortName: 'Canvas',
    website: '/',
    mail: '',
    phone: '',
    addressStreet: '',
    addressCity: ''
  };
  return {
    logo: {
      white: '',
      dark: ''
    },
    ...(brandRawConfig ? brandRawConfig : defaultBrand)
  };
}

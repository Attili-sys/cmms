import { LicenseEntitlement } from '../models/license';

export const useLicenseEntitlement = (_entitlement: LicenseEntitlement) => {
  // This mobile build is the unrestricted self-hosted edition. Keep the hook
  // signature for API compatibility while removing activation timing gates.
  return true;
};

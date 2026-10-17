package com.grash.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.grash.dto.license.LicenseEntitlement;
import com.grash.dto.license.LicensingState;
import com.grash.repository.KeygenRequestTrackerRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Arrays;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.verifyNoInteractions;

@ExtendWith(MockitoExtension.class)
class LicenseServiceTest {

    @Mock
    private KeygenRequestTrackerRepository keygenRequestTrackerRepository;

    private LicenseService licenseService;

    @BeforeEach
    void setUp() {
        licenseService = new LicenseService(new ObjectMapper(), keygenRequestTrackerRepository);
        ReflectionTestUtils.setField(licenseService, "cloudVersion", false);
        ReflectionTestUtils.setField(licenseService, "licenseKey", "must-not-be-used");
        ReflectionTestUtils.setField(licenseService, "licenseFilePath", "/missing/license.lic");
    }

    @Test
    void selfHostedStateGrantsEveryImplementedEntitlementWithoutActivation() {
        LicensingState state = licenseService.getLicensingState();

        assertTrue(state.isValid());
        assertFalse(state.isHasLicense());
        assertNull(state.getExpirationDate());
        assertTrue(Arrays.stream(LicenseEntitlement.values())
                .allMatch(entitlement -> state.getEntitlements().contains(entitlement.name())));
        verifyNoInteractions(keygenRequestTrackerRepository);
    }

    @Test
    void selfHostedEntitlementCheckDoesNotContactLicensingPersistence() {
        assertTrue(licenseService.hasEntitlement(LicenseEntitlement.UNLIMITED_USERS));
        assertTrue(licenseService.hasEntitlement(LicenseEntitlement.WORKFLOW));

        verifyNoInteractions(keygenRequestTrackerRepository);
    }
}

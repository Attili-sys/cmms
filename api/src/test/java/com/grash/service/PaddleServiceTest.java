package com.grash.service;

import com.grash.dto.checkout.CheckoutRequest;
import com.grash.exception.CustomException;
import com.grash.model.User;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.verifyNoInteractions;

@ExtendWith(MockitoExtension.class)
class PaddleServiceTest {

    @Mock
    private SubscriptionPlanService subscriptionPlanService;
    @Mock
    private WorkflowService workflowService;
    @Mock
    private UserService userService;
    @Mock
    private CacheService cacheService;

    private PaddleService paddleService;

    @BeforeEach
    void setUp() {
        paddleService = new PaddleService(subscriptionPlanService, workflowService, userService, cacheService);
        ReflectionTestUtils.setField(paddleService, "cloudVersion", false);
    }

    @Test
    void selfHostedCompanyCreationDoesNotUseBillingService() {
        assertDoesNotThrow(() -> paddleService.createCustomer(new User()));

        verifyNoInteractions(subscriptionPlanService, workflowService, userService, cacheService);
    }

    @Test
    void selfHostedCheckoutIsRejectedBeforeProcessingOrNetworkSetup() {
        CheckoutRequest request = new CheckoutRequest();

        CustomException exception = assertThrows(CustomException.class,
                () -> paddleService.createCheckoutSession(request, null));

        assertEquals(HttpStatus.NOT_FOUND, exception.getHttpStatus());
        verifyNoInteractions(subscriptionPlanService, workflowService, userService, cacheService);
    }
}

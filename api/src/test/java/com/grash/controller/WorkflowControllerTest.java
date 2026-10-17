package com.grash.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.grash.dto.WorkflowActionPostDTO;
import com.grash.dto.WorkflowPostDTO;
import com.grash.dto.WorkflowShowDTO;
import com.grash.dto.license.LicenseEntitlement;
import com.grash.mapper.WorkflowActionMapper;
import com.grash.mapper.WorkflowConditionMapper;
import com.grash.mapper.WorkflowMapper;
import com.grash.model.Company;
import com.grash.model.Role;
import com.grash.model.Subscription;
import com.grash.model.SubscriptionPlan;
import com.grash.model.User;
import com.grash.model.Workflow;
import com.grash.model.WorkflowAction;
import com.grash.model.enums.PermissionEntity;
import com.grash.model.enums.RoleType;
import com.grash.model.enums.workflow.WFMainCondition;
import com.grash.model.enums.workflow.WorkOrderAction;
import com.grash.service.LicenseService;
import com.grash.service.UserService;
import com.grash.service.WorkflowActionService;
import com.grash.service.WorkflowConditionService;
import com.grash.service.WorkflowService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static com.grash.utils.Helper.setCurrentUser;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(WorkflowController.class)
@AutoConfigureMockMvc(addFilters = false)
class WorkflowControllerTest extends AbstractControllerTest {

    @Autowired
    private MockMvc mockMvc;
    @Autowired
    private ObjectMapper objectMapper;
    @Autowired
    private LicenseService licenseService;

    @MockitoBean
    private WorkflowService workflowService;
    @MockitoBean
    private UserService userService;
    @MockitoBean
    private WorkflowConditionMapper workflowConditionMapper;
    @MockitoBean
    private WorkflowConditionService workflowConditionService;
    @MockitoBean
    private WorkflowActionMapper workflowActionMapper;
    @MockitoBean
    private WorkflowActionService workflowActionService;
    @MockitoBean
    private WorkflowMapper workflowMapper;

    private User user;
    private WorkflowPostDTO workflowRequest;

    @BeforeEach
    void setUp() {
        SubscriptionPlan legacyFreePlan = SubscriptionPlan.builder()
                .code("FREE")
                .features(new HashSet<>())
                .build();
        Subscription subscription = Subscription.builder()
                .subscriptionPlan(legacyFreePlan)
                .build();
        Company company = new Company("Test", 10, subscription);
        company.setId(1L);
        Role role = Role.builder()
                .roleType(RoleType.ROLE_CLIENT)
                .viewPermissions(new HashSet<>(Set.of(PermissionEntity.SETTINGS)))
                .build();
        user = new User();
        user.setId(1L);
        user.setEmail("owner@test.com");
        user.setEnabled(true);
        user.setCompany(company);
        user.setRole(role);

        workflowRequest = WorkflowPostDTO.builder()
                .title("Second workflow")
                .mainCondition(WFMainCondition.WORK_ORDER_CREATED)
                .secondaryConditions(List.of())
                .action(WorkflowActionPostDTO.builder()
                        .workOrderAction(WorkOrderAction.ASSIGN_PRIORITY)
                        .build())
                .build();
    }

    @Test
    void create_allowsMoreThanOneWorkflowOnLegacyFreePlan() throws Exception {
        Workflow existing = Workflow.builder().enabled(true).build();
        WorkflowAction action = new WorkflowAction();
        Workflow saved = Workflow.builder().title("Second workflow").enabled(true).build();
        WorkflowShowDTO response = new WorkflowShowDTO();
        response.setTitle("Second workflow");
        setCurrentUser(user);
        when(userService.whoami(any())).thenReturn(user);
        when(workflowService.findByCompany(1L)).thenReturn(List.of(existing));
        when(licenseService.hasEntitlement(LicenseEntitlement.WORKFLOW)).thenReturn(true);
        when(workflowActionMapper.toModel(workflowRequest.getAction())).thenReturn(action);
        when(workflowActionService.create(action)).thenReturn(action);
        when(workflowService.create(any(Workflow.class))).thenReturn(saved);
        when(workflowMapper.toShowDto(saved)).thenReturn(response);

        mockMvc.perform(post("/workflows")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(workflowRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Second workflow"));

        verify(workflowService).create(any(Workflow.class));
    }

    @Test
    void create_stillRejectsUserWithoutSettingsPermission() throws Exception {
        user.getRole().setViewPermissions(new HashSet<>());
        setCurrentUser(user);
        when(userService.whoami(any())).thenReturn(user);

        mockMvc.perform(post("/workflows")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(workflowRequest)))
                .andExpect(status().isForbidden());

        verify(workflowService, never()).create(any());
    }
}

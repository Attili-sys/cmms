import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  MenuItem,
  Stack,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
  useTheme
} from '@mui/material';
import Location from '../../../models/owns/location';
import { ChangeEvent, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import EditTwoToneIcon from '@mui/icons-material/EditTwoTone';
import DeleteTwoToneIcon from '@mui/icons-material/DeleteTwoTone';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AddTwoToneIcon from '@mui/icons-material/AddTwoTone';
import DownloadTwoToneIcon from '@mui/icons-material/DownloadTwoTone';
import FloorPlanViewer from './FloorPlanViewer';
import FloorPlan, {
  FloorPlanKind,
  floorPlanKinds
} from '../../../models/owns/floorPlan';
import { useDispatch, useSelector } from '../../../store';
import { getAssetsByLocation } from '../../../slices/asset';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getWorkOrdersByLocation } from '../../../slices/workOrder';
import {
  createFloorPlan,
  deleteFloorPlan,
  getFloorPlans
} from '../../../slices/floorPlan';
import { CompanySettingsContext } from '../../../contexts/CompanySettingsContext';
import { getAssetUrl } from '../../../utils/urlPaths';
import useAuth from '../../../hooks/useAuth';
import { PermissionEntity } from '../../../models/owns/role';
import { PlanFeature } from '../../../models/owns/subscriptionPlan';
import { CustomSnackBarContext } from '../../../contexts/CustomSnackBarContext';
import { getErrorMessage } from '../../../utils/api';

interface LocationDetailsProps {
  location: Location;
  handleOpenUpdate: () => void;
  handleOpenDelete: () => void;
  onCopy: (location: Location) => void;
}
export default function LocationDetails(props: LocationDetailsProps) {
  const { location, handleOpenUpdate, handleOpenDelete, onCopy } = props;
  const { t }: { t: any } = useTranslation();
  const dispatch = useDispatch();
  const { getFormattedDate, uploadFiles } = useContext(CompanySettingsContext);
  const { showSnackBar } = useContext(CustomSnackBarContext);
  const [openAddFloorPlan, setOpenAddFloorPlan] = useState<boolean>(false);
  const [currentTab, setCurrentTab] = useState<string>('assets');
  const [searchParams] = useSearchParams();
  const [showOlder, setShowOlder] = useState<boolean>(false);
  const [viewerPlanId, setViewerPlanId] = useState<number | null>(null);
  const [focusAssetId, setFocusAssetId] = useState<number | undefined>();
  const [deepLinkPlanId, setDeepLinkPlanId] = useState<number | null>(null);
  const [fpName, setFpName] = useState<string>('');
  const [fpArea, setFpArea] = useState<string>('');
  const [fpKind, setFpKind] = useState<string>('');
  const [fpRevision, setFpRevision] = useState<string>('');
  const [fpNote, setFpNote] = useState<string>('');
  const [fpFile, setFpFile] = useState<File | null>(null);
  const [fpSubmitting, setFpSubmitting] = useState<boolean>(false);
  const { assetsByLocation } = useSelector((state) => state.assets);
  const { workOrdersByLocation } = useSelector((state) => state.workOrders);
  const { floorPlansByLocation } = useSelector((state) => state.floorPlans);
  const {
    hasEditPermission,
    hasDeletePermission,
    hasCreatePermission,
    hasFeature
  } = useAuth();
  const locationAssets = assetsByLocation[location.id] ?? [];
  const locationWorkOrders = workOrdersByLocation[location.id] ?? [];
  // All revisions are loaded; older ones are hidden unless asked for, and the switch only
  // appears when there is an older revision to show.
  const allFloorPlans = floorPlansByLocation[location.id] ?? [];
  const hasOlderRevisions = allFloorPlans.some((plan) => plan.current === false);
  const floorPlans = showOlder
    ? allFloorPlans
    : allFloorPlans.filter((plan) => plan.current !== false);
  const theme = useTheme();
  const navigate = useNavigate();
  const tabs = [
    { value: 'assets', label: t('assets') },
    { value: 'files', label: t('files') },
    { value: 'workOrders', label: t('work_orders') },
    { value: 'floorPlans', label: t('floor_plans') },
    { value: 'people', label: t('people') }
  ];

  const kindLabel = (kind?: FloorPlanKind | null) =>
    kind
      ? t(`floor_plan_kind_${kind.toLowerCase()}`)
      : t('floor_plan_kind_unspecified');
  const canEditLocation = hasEditPermission(
    PermissionEntity.LOCATIONS,
    location
  );
  const viewerPlan: FloorPlan | undefined = floorPlans.find(
    (plan) => plan.id === viewerPlanId
  );

  const resetFloorPlanForm = () => {
    setFpName('');
    setFpArea('');
    setFpKind('');
    setFpRevision('');
    setFpNote('');
    setFpFile(null);
  };

  const submitFloorPlan = async () => {
    if (!fpName.trim() || !fpFile) return;
    setFpSubmitting(true);
    try {
      const isImage = fpFile.type.startsWith('image/');
      const uploaded = await uploadFiles(
        isImage ? [] : ([fpFile] as any),
        isImage ? ([fpFile] as any) : []
      );
      if (!uploaded.length) return;
      const body: { [key: string]: any } = {
        name: fpName.trim(),
        kind: fpKind || null,
        revision: fpRevision.trim() || null,
        note: fpNote.trim() || null,
        [isImage ? 'image' : 'file']: { id: uploaded[0].id }
      };
      if (fpArea !== '') body.area = Number(fpArea);
      await dispatch(createFloorPlan(location.id, body));
      await dispatch(getFloorPlans(location.id, true));
      resetFloorPlanForm();
      setOpenAddFloorPlan(false);
    } catch (err) {
      showSnackBar(getErrorMessage(err), 'error');
    } finally {
      setFpSubmitting(false);
    }
  };

  useEffect(() => {
    dispatch(getAssetsByLocation(location.id));
    dispatch(getWorkOrdersByLocation(location.id));
  }, [location]);

  useEffect(() => {
    dispatch(getFloorPlans(location.id, true));
  }, [location]);

  // deep link: ?tab=floorPlans&floorPlan=<id>&asset=<assetId>
  const searchString = searchParams.toString();
  useEffect(() => {
    const tab = searchParams.get('tab');
    const planParam = searchParams.get('floorPlan');
    const assetParam = searchParams.get('asset');
    if (tab === 'floorPlans' || planParam) setCurrentTab('floorPlans');
    if (planParam && Number.isFinite(Number(planParam))) {
      setDeepLinkPlanId(Number(planParam));
      setFocusAssetId(
        assetParam && Number.isFinite(Number(assetParam))
          ? Number(assetParam)
          : undefined
      );
    }
  }, [location.id, searchString]);

  useEffect(() => {
    if (!deepLinkPlanId) return;
    const found = allFloorPlans.find((plan) => plan.id === deepLinkPlanId);
    if (found) {
      if (found.current === false) setShowOlder(true);
      setViewerPlanId(found.id);
      setDeepLinkPlanId(null);
    }
  }, [deepLinkPlanId, floorPlansByLocation, location.id]);

  const renderAddFloorPlanModal = () => (
    <Dialog
      fullWidth
      maxWidth="sm"
      open={openAddFloorPlan}
      onClose={() => setOpenAddFloorPlan(false)}
    >
      <DialogTitle
        sx={{
          p: 3
        }}
      >
        <Typography variant="h4" gutterBottom>
          {t('add_floor_plan')}
        </Typography>
        <Typography variant="subtitle2">
          {t('add_floor_plan_description')}
        </Typography>
      </DialogTitle>
      <DialogContent
        dividers
        sx={{
          p: 3
        }}
      >
        <Stack spacing={2}>
          <TextField
            required
            fullWidth
            label={t('name')}
            placeholder={t('floor_plan_name_description')}
            value={fpName}
            onChange={(e) => setFpName(e.target.value)}
            error={!fpName.trim() && fpSubmitting}
          />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              select
              fullWidth
              label={t('floor_plan_kind')}
              value={fpKind}
              onChange={(e) => setFpKind(e.target.value)}
            >
              <MenuItem value="">{t('floor_plan_kind_unspecified')}</MenuItem>
              {floorPlanKinds.map((kind) => (
                <MenuItem key={kind} value={kind}>
                  {kindLabel(kind)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              label={t('floor_plan_revision')}
              value={fpRevision}
              onChange={(e) => setFpRevision(e.target.value)}
            />
          </Stack>
          <TextField
            fullWidth
            type="number"
            label={t('area')}
            value={fpArea}
            onChange={(e) => setFpArea(e.target.value)}
          />
          <TextField
            fullWidth
            multiline
            minRows={2}
            label={t('floor_plan_note')}
            value={fpNote}
            onChange={(e) => setFpNote(e.target.value)}
          />
          <Box>
            <Button variant="outlined" component="label">
              {t('floor_plan_choose_file')}
              <input
                hidden
                type="file"
                accept="image/*,application/pdf"
                onChange={(e) => setFpFile(e.target.files?.[0] ?? null)}
              />
            </Button>
            <Typography variant="body2" sx={{ mt: 1 }}>
              {fpFile ? fpFile.name : t('floor_plan_file_hint')}
            </Typography>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={() => setOpenAddFloorPlan(false)}>
          {t('cancel')}
        </Button>
        <Button
          variant="contained"
          disabled={fpSubmitting || !fpName.trim() || !fpFile}
          onClick={submitFloorPlan}
        >
          {t('add_floor_plan')}
        </Button>
      </DialogActions>
    </Dialog>
  );
  const handleTabsChange = (_event: ChangeEvent<{}>, value: string): void => {
    setCurrentTab(value);
  };
  return (
    <Grid
      container
      justifyContent="center"
      alignItems="stretch"
      spacing={2}
      padding={{ xs: 2, md: 4 }}
    >
      {renderAddFloorPlanModal()}
      <Grid
        item
        xs={12}
        display="flex"
        flexDirection="row"
        justifyContent="space-between"
      >
        <Box>
          <Typography variant="h2">{location?.name}</Typography>
          <Typography variant="h6">{location?.address}</Typography>
        </Box>
        <Box>
          {hasEditPermission(PermissionEntity.LOCATIONS, location) && (
            <IconButton onClick={handleOpenUpdate} style={{ marginRight: 10 }}>
              <EditTwoToneIcon color="primary" />
            </IconButton>
          )}
          {hasCreatePermission(PermissionEntity.LOCATIONS) && (
            <IconButton
              style={{ marginRight: 10 }}
              onClick={() => onCopy(location)}
            >
              <ContentCopyIcon color="primary" />
            </IconButton>
          )}
          {hasDeletePermission(PermissionEntity.LOCATIONS, location) && (
            <IconButton onClick={handleOpenDelete}>
              <DeleteTwoToneIcon color="error" />
            </IconButton>
          )}
        </Box>
      </Grid>
      <Divider />
      {location.image && (
        <Grid
          item
          xs={12}
          lg={12}
          display="flex"
          justifyContent="center"
          padding={2}
        >
          <img
            src={location.image.url}
            style={{ borderRadius: 5, height: 200 }}
          />
        </Grid>
      )}
      <Grid item xs={12}>
        <Tabs
          onChange={handleTabsChange}
          value={currentTab}
          variant="scrollable"
          scrollButtons="auto"
          textColor="primary"
          indicatorColor="primary"
        >
          {tabs.map((tab) => (
            <Tab key={tab.value} label={tab.label} value={tab.value} />
          ))}
        </Tabs>
      </Grid>
      <Grid item xs={12}>
        {currentTab === 'assets' && (
          <Box>
            {hasCreatePermission(PermissionEntity.ASSETS) && (
              <Box display="flex" justifyContent="right">
                <Button
                  startIcon={<AddTwoToneIcon fontSize="small" />}
                  onClick={() =>
                    navigate(`/app/assets?location=${location.id}`)
                  }
                >
                  {t('asset')}
                </Button>
              </Box>
            )}
            {locationAssets.length ? (
              <List sx={{ width: '100%' }}>
                {locationAssets.map((asset) => (
                  <ListItemButton
                    key={asset.id}
                    divider
                    onClick={() => navigate(getAssetUrl(asset.id))}
                  >
                    <ListItemText
                      primary={asset.name}
                      secondary={getFormattedDate(asset.createdAt)}
                    />
                  </ListItemButton>
                ))}
              </List>
            ) : (
              <Stack direction="row" justifyContent="center" width="100%">
                <Typography variant="h5">
                  {t('no_asset_in_location')}
                </Typography>
              </Stack>
            )}
          </Box>
        )}
        {currentTab === 'workOrders' && (
          <Box>
            {hasCreatePermission(PermissionEntity.WORK_ORDERS) && (
              <Box display="flex" justifyContent="right">
                <Button
                  startIcon={<AddTwoToneIcon fontSize="small" />}
                  onClick={() =>
                    navigate(`/app/work-orders?location=${location.id}`)
                  }
                >
                  {t('work_order')}
                </Button>
              </Box>
            )}
            {locationWorkOrders.length ? (
              <List sx={{ width: '100%' }}>
                {locationWorkOrders.map((workOrder) => (
                  <ListItemButton
                    key={workOrder.id}
                    divider
                    onClick={() => navigate(`/app/work-orders/${workOrder.id}`)}
                  >
                    <ListItemText
                      primary={workOrder.title}
                      secondary={getFormattedDate(workOrder.createdAt)}
                    />
                  </ListItemButton>
                ))}
              </List>
            ) : (
              <Stack direction="row" justifyContent="center" width="100%">
                <Typography variant="h5">{t('no_wo_in_location')}</Typography>
              </Stack>
            )}
          </Box>
        )}
        {currentTab === 'files' && (
          <Box>
            {hasCreatePermission(PermissionEntity.FILES) &&
              hasFeature(PlanFeature.FILE) && (
                <Box display="flex" justifyContent="right">
                  <Button
                    startIcon={<AddTwoToneIcon fontSize="small" />}
                    onClick={handleOpenUpdate}
                  >
                    {t('file')}
                  </Button>
                </Box>
              )}
            {location.files.length ? (
              <List sx={{ width: '100%' }}>
                {location.files.map((file) => (
                  <ListItemButton
                    key={file.id}
                    divider
                    onClick={() => window.open(file.url, '_blank')}
                  >
                    <ListItemText
                      primary={
                        <Typography variant="h6" fontWeight="bold">
                          {file.name}
                        </Typography>
                      }
                    />
                  </ListItemButton>
                ))}
              </List>
            ) : (
              <Stack direction="row" justifyContent="center" width="100%">
                <Typography variant="h5">{t('no_file_in_location')}</Typography>
              </Stack>
            )}
          </Box>
        )}
        {currentTab === 'floorPlans' && (
          <Box>
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              flexWrap="wrap"
            >
              {hasOlderRevisions ? (
                <FormControlLabel
                  control={
                    <Switch
                      checked={showOlder}
                      onChange={(e) => setShowOlder(e.target.checked)}
                    />
                  }
                  label={t('show_older_revisions')}
                />
              ) : (
                <span />
              )}
              {canEditLocation && (
                <Button
                  onClick={() => setOpenAddFloorPlan(true)}
                  startIcon={<AddTwoToneIcon fontSize="small" />}
                >
                  {t('floor_plan')}
                </Button>
              )}
            </Stack>
            {viewerPlan && (
              <Box sx={{ my: 2 }}>
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  sx={{ mb: 1 }}
                >
                  <Typography variant="h5">
                    {viewerPlan.name}
                    {viewerPlan.revision ? ` (${viewerPlan.revision})` : ''}
                  </Typography>
                  <Button
                    size="small"
                    onClick={() => {
                      setViewerPlanId(null);
                      setFocusAssetId(undefined);
                    }}
                  >
                    {t('close_floor_plan')}
                  </Button>
                </Stack>
                <FloorPlanViewer
                  key={viewerPlan.id}
                  floorPlan={viewerPlan}
                  canEdit={canEditLocation}
                  focusAssetId={focusAssetId}
                />
              </Box>
            )}
            {floorPlans.length ? (
              <List sx={{ width: '100%' }}>
                {floorPlans.map((floorPlan) => (
                  <ListItemButton
                    key={floorPlan.id}
                    divider
                    selected={floorPlan.id === viewerPlanId}
                    onClick={() => {
                      setFocusAssetId(undefined);
                      setViewerPlanId(floorPlan.id);
                    }}
                  >
                    <ListItem
                      disableGutters
                      secondaryAction={
                        <Stack direction="row" alignItems="center">
                          {floorPlan.sourceFile?.url && (
                            <Link
                              href={floorPlan.sourceFile.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              sx={{ display: 'inline-flex', mr: 1 }}
                              title={t('download_original')}
                            >
                              <DownloadTwoToneIcon fontSize="small" />
                            </Link>
                          )}
                          {canEditLocation && (
                            <IconButton
                              sx={{ ml: 1 }}
                              onClick={(e) => {
                                e.stopPropagation();
                                if (
                                  window.confirm(
                                    t(
                                      "Are you sure you want to delete this Floor Plan. It can't be undone"
                                    )
                                  )
                                ) {
                                  if (floorPlan.id === viewerPlanId)
                                    setViewerPlanId(null);
                                  dispatch(
                                    deleteFloorPlan(location.id, floorPlan.id)
                                  );
                                }
                              }}
                            >
                              <DeleteTwoToneIcon
                                fontSize="small"
                                color="error"
                              />
                            </IconButton>
                          )}
                        </Stack>
                      }
                    >
                      <ListItemText
                        primary={floorPlan.name}
                        secondaryTypographyProps={{ component: 'div' }}
                        secondary={
                          <Stack
                            direction="row"
                            spacing={1}
                            alignItems="center"
                            flexWrap="wrap"
                          >
                            <span>{kindLabel(floorPlan.kind)}</span>
                            {floorPlan.revision && (
                              <span>
                                {t('floor_plan_revision')}: {floorPlan.revision}
                              </span>
                            )}
                            <span>
                              {t('floor_plan_pin_count', {
                                count: floorPlan.pinCount ?? 0
                              })}
                            </span>
                            {floorPlan.area ? (
                              <span>{`${floorPlan.area} m²`}</span>
                            ) : null}
                            <Chip
                              size="small"
                              color={
                                floorPlan.current === false
                                  ? 'default'
                                  : 'success'
                              }
                              label={
                                floorPlan.current === false
                                  ? t('floor_plan_superseded')
                                  : t('floor_plan_current')
                              }
                            />
                          </Stack>
                        }
                      />
                    </ListItem>
                  </ListItemButton>
                ))}
              </List>
            ) : (
              <Stack direction="row" justifyContent="center" width="100%">
                <Typography variant="h5">
                  {t('no_floor_plan_in_location')}
                </Typography>
              </Stack>
            )}
          </Box>
        )}
        {currentTab === 'people' && (
          <Grid container>
            {!!location.workers.length && (
              <Grid item xs={12} lg={6}>
                <Typography
                  variant="h6"
                  sx={{ color: theme.colors.alpha.black[70] }}
                >
                  {t('assigned_to')}
                </Typography>
                {location.workers.map((worker, index) => (
                  <Box key={worker.id}>
                    <Link
                      href={`/app/people-teams/people/${worker.id}`}
                      variant="h6"
                      fontWeight="bold"
                    >
                      {`${worker.firstName} ${worker.lastName}`}
                    </Link>
                  </Box>
                ))}
              </Grid>
            )}
            {!!location.teams.length && (
              <Grid item xs={12} lg={6}>
                <Typography
                  variant="h6"
                  sx={{ color: theme.colors.alpha.black[70] }}
                >
                  {t('assigned_teams')}
                </Typography>
                {location.teams.map((team, index) => (
                  <Box key={team.id}>
                    <Link
                      href={`/app/people-teams/teams/${team.id}`}
                      variant="h6"
                      fontWeight="bold"
                    >
                      {team.name}
                    </Link>
                  </Box>
                ))}
              </Grid>
            )}
            {!!location.customers.length && (
              <Grid item xs={12} lg={6}>
                <Typography
                  variant="h6"
                  sx={{ color: theme.colors.alpha.black[70] }}
                >
                  {t('assigned_customers')}
                </Typography>
                {location.customers.map((customer, index) => (
                  <Box key={customer.id}>
                    <Link
                      href={`/app/vendors-customers/customers/${customer.id}`}
                      variant="h6"
                      fontWeight="bold"
                    >
                      {customer.name}
                    </Link>
                  </Box>
                ))}
              </Grid>
            )}
            {!!location.vendors.length && (
              <Grid item xs={12} lg={6}>
                <Typography
                  variant="h6"
                  sx={{ color: theme.colors.alpha.black[70] }}
                >
                  {t('assigned_vendors')}
                </Typography>
                {location.vendors.map((vendor, index) => (
                  <Box key={vendor.id}>
                    <Link
                      href={`/app/vendors-customers/vendors/${vendor.id}`}
                      variant="h6"
                      fontWeight="bold"
                    >
                      {vendor.companyName}
                    </Link>
                  </Box>
                ))}
              </Grid>
            )}
          </Grid>
        )}
      </Grid>
    </Grid>
  );
}

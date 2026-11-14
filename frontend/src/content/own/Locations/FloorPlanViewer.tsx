import {
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Popover,
  Stack,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import PlaceTwoToneIcon from '@mui/icons-material/PlaceTwoTone';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import FloorPlan, {
  FloorPlanPin,
  PinnableAsset
} from '../../../models/owns/floorPlan';
import { useDispatch, useSelector } from '../../../store';
import {
  deletePin,
  getPinnableAssets,
  getPins,
  upsertPin
} from '../../../slices/floorPlan';
import { getAssetUrl } from '../../../utils/urlPaths';

type StatusColor = 'success' | 'error' | 'warning' | 'info' | 'default';

const statusColor = (status: string): StatusColor => {
  switch (status) {
    case 'OPERATIONAL':
      return 'success';
    case 'DOWN':
    case 'EMERGENCY_SHUTDOWN':
      return 'error';
    case 'INSPECTION_SCHEDULED':
    case 'MODERNIZATION':
      return 'warning';
    case 'STANDBY':
    case 'COMMISSIONING':
      return 'info';
    default:
      return 'default';
  }
};

const legend: { color: StatusColor; label: string }[] = [
  { color: 'success', label: 'operational' },
  { color: 'error', label: 'down' },
  { color: 'warning', label: 'floor_plan_legend_attention' },
  { color: 'info', label: 'floor_plan_legend_standby' }
];

const humanize = (s: string) =>
  (s ?? '')
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/^\w/, (c) => c.toUpperCase());

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 4;
const DRAG_THRESHOLD = 4; // px

const clamp = (v: number, min: number, max: number) =>
  Math.min(max, Math.max(min, v));

interface Props {
  floorPlan: FloorPlan;
  canEdit: boolean;
  focusAssetId?: number;
}

interface DragState {
  assetId: number;
  startX: number;
  startY: number;
  moved: boolean;
}

export default function FloorPlanViewer({
  floorPlan,
  canEdit,
  focusAssetId
}: Props) {
  const { t }: { t: any } = useTranslation();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const pins: FloorPlanPin[] =
    useSelector((state) => state.floorPlans.pinsByFloorPlan[floorPlan.id]) ??
    [];
  const [loading, setLoading] = useState<boolean>(true);
  const [zoom, setZoom] = useState<number>(1);
  const [placing, setPlacing] = useState<PinnableAsset | null>(null);
  const [options, setOptions] = useState<PinnableAsset[]>([]);
  const [search, setSearch] = useState<string>('');
  const [dragPos, setDragPos] = useState<{
    assetId: number;
    x: number;
    y: number;
  } | null>(null);
  const [popover, setPopover] = useState<{
    el: HTMLElement;
    pin: FloorPlanPin;
  } | null>(null);
  const [highlightId, setHighlightId] = useState<number | undefined>(
    focusAssetId
  );
  const scrollRef = useRef<HTMLDivElement>(null);
  const imageBoxRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const pinRefs = useRef<{ [assetId: number]: HTMLElement | null }>({});
  const editable = canEdit && floorPlan.current !== false;
  const imageUrl = floorPlan.image?.url;

  useEffect(() => {
    setLoading(true);
    Promise.resolve(dispatch(getPins(floorPlan.id))).finally(() =>
      setLoading(false)
    );
  }, [floorPlan.id]);

  useEffect(() => {
    setHighlightId(focusAssetId);
  }, [focusAssetId, floorPlan.id]);

  // scroll to the focused pin once pins are loaded
  useEffect(() => {
    if (!highlightId || loading) return;
    const el = pinRefs.current[highlightId];
    const box = scrollRef.current;
    if (el && box) {
      // Scroll only the viewer's own box: scrollIntoView would also shift the drawer and page.
      const pin = el.getBoundingClientRect();
      const frame = box.getBoundingClientRect();
      box.scrollBy({
        left: pin.left - frame.left - frame.width / 2,
        top: pin.top - frame.top - frame.height / 2
      });
    }
  }, [highlightId, loading, pins.length]);

  // debounced pinnable asset search
  useEffect(() => {
    if (!editable) return;
    const handle = setTimeout(() => {
      Promise.resolve(dispatch(getPinnableAssets(floorPlan.id, search)))
        .then((result) => setOptions(Array.isArray(result) ? result : []))
        .catch(() => setOptions([]));
    }, 300);
    return () => clearTimeout(handle);
  }, [search, floorPlan.id, editable, pins.length]);

  // ctrl / cmd + wheel zoom (needs a non passive listener)
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      e.preventDefault();
      setZoom((z) =>
        clamp(z * (e.deltaY < 0 ? 1.1 : 1 / 1.1), MIN_ZOOM, MAX_ZOOM)
      );
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, []);

  const toFraction = (clientX: number, clientY: number) => {
    const rect = imageBoxRef.current?.getBoundingClientRect();
    if (!rect || !rect.width || !rect.height) return null;
    // physical coordinates: always measured from the image's left/top edge
    return {
      x: clamp((clientX - rect.left) / rect.width, 0, 1),
      y: clamp((clientY - rect.top) / rect.height, 0, 1)
    };
  };

  const handleImageClick = (e: React.MouseEvent) => {
    if (!placing || !editable) return;
    const f = toFraction(e.clientX, e.clientY);
    if (!f) return;
    const asset = placing;
    setPlacing(null);
    setSearch('');
    dispatch(upsertPin(floorPlan.id, asset.id, f.x, f.y)).then(() =>
      setHighlightId(asset.id)
    );
  };

  const onPinPointerDown = (e: ReactPointerEvent, pin: FloorPlanPin) => {
    e.stopPropagation();
    if (!editable) return;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    dragRef.current = {
      assetId: pin.asset.id,
      startX: e.clientX,
      startY: e.clientY,
      moved: false
    };
  };

  const onPinPointerMove = (e: ReactPointerEvent) => {
    const drag = dragRef.current;
    if (!drag) return;
    if (
      !drag.moved &&
      Math.hypot(e.clientX - drag.startX, e.clientY - drag.startY) <
        DRAG_THRESHOLD
    )
      return;
    drag.moved = true;
    const f = toFraction(e.clientX, e.clientY);
    if (f) setDragPos({ assetId: drag.assetId, ...f });
  };

  const onPinPointerUp = (e: ReactPointerEvent, pin: FloorPlanPin) => {
    const drag = dragRef.current;
    dragRef.current = null;
    const el = e.currentTarget as HTMLElement;
    if (el.hasPointerCapture?.(e.pointerId))
      el.releasePointerCapture(e.pointerId);
    if (drag?.moved) {
      const f = toFraction(e.clientX, e.clientY);
      if (f) {
        dispatch(upsertPin(floorPlan.id, pin.asset.id, f.x, f.y)).finally(() =>
          setDragPos(null)
        );
      } else setDragPos(null);
    } else {
      setDragPos(null);
      setPopover({ el, pin });
    }
  };

  const onPinPointerCancel = () => {
    dragRef.current = null;
    setDragPos(null);
  };

  const popoverPin = useMemo(
    () =>
      popover ? pins.find((p) => p.asset.id === popover.pin.asset.id) : null,
    [popover, pins]
  );

  return (
    <Box>
      <Stack
        direction="row"
        spacing={1}
        alignItems="center"
        flexWrap="wrap"
        sx={{ mb: 1 }}
      >
        <Tooltip title={t('zoom_out')}>
          <span>
            <IconButton
              size="small"
              disabled={zoom <= MIN_ZOOM}
              onClick={() =>
                setZoom((z) => clamp(z / 1.25, MIN_ZOOM, MAX_ZOOM))
              }
            >
              <RemoveIcon />
            </IconButton>
          </span>
        </Tooltip>
        <Typography variant="body2" sx={{ minWidth: 44, textAlign: 'center' }}>
          {Math.round(zoom * 100)}%
        </Typography>
        <Tooltip title={t('zoom_in')}>
          <span>
            <IconButton
              size="small"
              disabled={zoom >= MAX_ZOOM}
              onClick={() =>
                setZoom((z) => clamp(z * 1.25, MIN_ZOOM, MAX_ZOOM))
              }
            >
              <AddIcon />
            </IconButton>
          </span>
        </Tooltip>
        <Button size="small" onClick={() => setZoom(1)}>
          {t('reset_zoom')}
        </Button>
        {editable && (
          <Autocomplete<PinnableAsset, false, false, false>
            size="small"
            sx={{ minWidth: 220, flexGrow: 1, maxWidth: 360 }}
            options={options}
            value={placing}
            getOptionLabel={(o) =>
              o.customId ? `${o.name} (${o.customId})` : o.name
            }
            isOptionEqualToValue={(a, b) => a.id === b.id}
            filterOptions={(x) => x}
            onInputChange={(_e, value, reason) => {
              if (reason === 'input') setSearch(value);
            }}
            onChange={(_e, value) => setPlacing(value)}
            renderInput={(params) => (
              <TextField {...params} label={t('place_asset')} />
            )}
          />
        )}
      </Stack>
      {placing && editable && (
        <Typography variant="caption" color="primary" display="block" mb={1}>
          {t('click_plan_to_place_asset', { name: placing.name })}
        </Typography>
      )}
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} flexWrap="wrap">
        {legend.map((l) => (
          <Chip
            key={l.label}
            size="small"
            variant="outlined"
            color={l.color}
            label={t(l.label)}
          />
        ))}
      </Stack>
      {!editable && (
        <Typography
          variant="caption"
          color="text.secondary"
          display="block"
          mb={1}
        >
          {floorPlan.current === false
            ? t('floor_plan_superseded_read_only')
            : t('floor_plan_read_only')}
        </Typography>
      )}
      <Box
        ref={scrollRef}
        dir="ltr"
        sx={{
          position: 'relative',
          overflow: 'auto',
          maxHeight: { xs: '60vh', md: '70vh' },
          border: 1,
          borderColor: 'divider',
          borderRadius: 1,
          bgcolor: 'action.hover',
          touchAction: 'pan-x pan-y'
        }}
      >
        {loading && (
          <Box sx={{ position: 'absolute', top: 8, left: 8, zIndex: 3 }}>
            <CircularProgress size={20} />
          </Box>
        )}
        {imageUrl ? (
          <Box
            ref={imageBoxRef}
            onClick={handleImageClick}
            sx={{
              position: 'relative',
              width: `${zoom * 100}%`,
              cursor: placing && editable ? 'crosshair' : 'default',
              lineHeight: 0,
              userSelect: 'none'
            }}
          >
            <img
              src={imageUrl}
              alt={floorPlan.name}
              draggable={false}
              style={{ width: '100%', display: 'block' }}
            />
            {pins.map((pin) => {
              const pos =
                dragPos && dragPos.assetId === pin.asset.id ? dragPos : pin;
              const color = statusColor(pin.asset.status);
              const highlighted = highlightId === pin.asset.id;
              return (
                <Box
                  key={pin.asset.id}
                  ref={(el: HTMLElement | null) => {
                    pinRefs.current[pin.asset.id] = el;
                  }}
                  onClick={(e) => e.stopPropagation()}
                  onPointerDown={(e) => onPinPointerDown(e, pin)}
                  onPointerMove={onPinPointerMove}
                  onPointerUp={(e) => onPinPointerUp(e, pin)}
                  onPointerCancel={onPinPointerCancel}
                  // Inline, not sx: the app's RTL style plugin flips `left` to `right` in emotion
                  // styles, which would mirror every pin in Arabic. Coordinates are physical.
                  style={{
                    left: `${pos.x * 100}%`,
                    top: `${pos.y * 100}%`,
                    transform: 'translate(-50%, -100%)'
                  }}
                  sx={{
                    position: 'absolute',
                    lineHeight: 1,
                    cursor: editable ? 'grab' : 'pointer',
                    touchAction: editable ? 'none' : 'auto',
                    zIndex: highlighted ? 2 : 1,
                    color:
                      color === 'default' ? 'text.secondary' : `${color}.main`,
                    filter: highlighted
                      ? 'drop-shadow(0 0 6px rgba(255,193,7,1))'
                      : 'drop-shadow(0 1px 1px rgba(0,0,0,0.5))',
                    animation: highlighted
                      ? 'fpPulse 1s ease-in-out 3'
                      : 'none',
                    '@keyframes fpPulse': {
                      '0%,100%': {
                        transform: 'translate(-50%,-100%) scale(1)'
                      },
                      '50%': { transform: 'translate(-50%,-100%) scale(1.4)' }
                    }
                  }}
                  title={pin.asset.name}
                >
                  <PlaceTwoToneIcon
                    sx={{ fontSize: 32, display: 'block' }}
                    htmlColor="currentColor"
                  />
                </Box>
              );
            })}
          </Box>
        ) : (
          <Typography sx={{ p: 3 }} color="text.secondary">
            {t('floor_plan_no_image')}
          </Typography>
        )}
      </Box>
      <Popover
        open={!!popover && !!popoverPin}
        anchorEl={popover?.el}
        onClose={() => setPopover(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        transformOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {popoverPin && (
          <Stack spacing={1} sx={{ p: 2, maxWidth: 280 }}>
            <Typography variant="h6">{popoverPin.asset.name}</Typography>
            {popoverPin.asset.customId && (
              <Typography variant="body2" color="text.secondary">
                {popoverPin.asset.customId}
              </Typography>
            )}
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip
                size="small"
                color={statusColor(popoverPin.asset.status)}
                label={t(popoverPin.asset.status?.toLowerCase(), {
                  defaultValue: humanize(popoverPin.asset.status)
                })}
              />
              <Typography variant="body2">
                {t('open_work_orders_count', {
                  count: popoverPin.asset.openWorkOrders ?? 0
                })}
              </Typography>
            </Stack>
            <Stack direction="row" spacing={1}>
              <Button
                size="small"
                variant="contained"
                onClick={() => navigate(getAssetUrl(popoverPin.asset.id))}
              >
                {t('open_asset')}
              </Button>
              {editable && (
                <Button
                  size="small"
                  color="error"
                  onClick={() => {
                    if (window.confirm(t('confirm_remove_pin'))) {
                      const assetId = popoverPin.asset.id;
                      setPopover(null);
                      dispatch(deletePin(floorPlan.id, assetId));
                    }
                  }}
                >
                  {t('remove_pin')}
                </Button>
              )}
            </Stack>
          </Stack>
        )}
      </Popover>
    </Box>
  );
}

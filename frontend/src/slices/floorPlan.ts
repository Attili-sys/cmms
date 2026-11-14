import type { PayloadAction } from '@reduxjs/toolkit';
import { createSlice } from '@reduxjs/toolkit';
import type { AppThunk } from 'src/store';
import FloorPlan, {
  AssetFloorPlanPin,
  FloorPlanPin,
  PinnableAsset
} from '../models/owns/floorPlan';
import api from '../utils/api';
import { revertAll } from 'src/utils/redux';

const basePath = 'floor-plans';
interface FloorPlanState {
  floorPlansByLocation: { [id: number]: FloorPlan[] };
  pinsByFloorPlan: { [id: number]: FloorPlanPin[] };
}

const initialState: FloorPlanState = {
  floorPlansByLocation: {},
  pinsByFloorPlan: {}
};

const slice = createSlice({
  name: 'floorPlans',
  initialState,
  extraReducers: (builder) => builder.addCase(revertAll, () => initialState),
  reducers: {
    getFloorPlans(
      state: FloorPlanState,
      action: PayloadAction<{ id: number; floorPlans: FloorPlan[] }>
    ) {
      const { floorPlans, id } = action.payload;
      state.floorPlansByLocation[id] = floorPlans;
    },
    createFloorPlan(
      state: FloorPlanState,
      action: PayloadAction<{
        locationId: number;
        floorPlan: FloorPlan;
      }>
    ) {
      const { floorPlan, locationId } = action.payload;
      state.floorPlansByLocation[locationId] = [
        ...(state.floorPlansByLocation[locationId] ?? []),
        floorPlan
      ];
    },
    deleteFloorPlan(
      state: FloorPlanState,
      action: PayloadAction<{
        locationId: number;
        id: number;
      }>
    ) {
      const { id, locationId } = action.payload;
      state.floorPlansByLocation[locationId] = (
        state.floorPlansByLocation[locationId] ?? []
      ).filter((floorPlan) => floorPlan.id !== id);
      delete state.pinsByFloorPlan[id];
    },
    setPins(
      state: FloorPlanState,
      action: PayloadAction<{ id: number; pins: FloorPlanPin[] }>
    ) {
      state.pinsByFloorPlan[action.payload.id] = action.payload.pins;
    },
    upsertPin(
      state: FloorPlanState,
      action: PayloadAction<{ id: number; pin: FloorPlanPin }>
    ) {
      const { id, pin } = action.payload;
      const pins = state.pinsByFloorPlan[id] ?? [];
      const index = pins.findIndex((p) => p.asset.id === pin.asset.id);
      if (index >= 0) pins[index] = pin;
      else pins.push(pin);
      state.pinsByFloorPlan[id] = pins;
    },
    removePin(
      state: FloorPlanState,
      action: PayloadAction<{ id: number; assetId: number }>
    ) {
      const { id, assetId } = action.payload;
      state.pinsByFloorPlan[id] = (state.pinsByFloorPlan[id] ?? []).filter(
        (p) => p.asset.id !== assetId
      );
    },
    adjustPinCount(
      state: FloorPlanState,
      action: PayloadAction<{ id: number; delta: number }>
    ) {
      const { id, delta } = action.payload;
      Object.values(state.floorPlansByLocation).forEach((plans) =>
        plans.forEach((plan) => {
          if (plan.id === id) {
            plan.pinCount = Math.max(0, (plan.pinCount ?? 0) + delta);
          }
        })
      );
    }
  }
});

export const reducer = slice.reducer;

export const getFloorPlans =
  (id: number, includeSuperseded?: boolean): AppThunk =>
  async (dispatch) => {
    const floorPlans = await api.get<FloorPlan[]>(
      `${basePath}/location/${id}?includeSuperseded=${!!includeSuperseded}`
    );
    dispatch(slice.actions.getFloorPlans({ id, floorPlans }));
  };

export const createFloorPlan =
  (
    id: number,
    floorPlan: Partial<FloorPlan> & { [key: string]: any }
  ): AppThunk =>
  async (dispatch) => {
    const floorPlanResponse = await api.post<FloorPlan>(`${basePath}`, {
      ...floorPlan,
      location: { id }
    });
    dispatch(
      slice.actions.createFloorPlan({
        locationId: id,
        floorPlan: floorPlanResponse
      })
    );
    // a new revision may supersede an older plan: refresh
    await dispatch(getFloorPlans(id));
  };

export const deleteFloorPlan =
  (locationId: number, id: number): AppThunk =>
  async (dispatch) => {
    const response = await api.deletes<{ success: boolean }>(
      `${basePath}/${id}`
    );
    const { success } = response;
    if (success) {
      dispatch(slice.actions.deleteFloorPlan({ locationId, id }));
    }
  };

export const getPins =
  (floorPlanId: number): AppThunk =>
  async (dispatch) => {
    const pins = await api.get<FloorPlanPin[]>(
      `${basePath}/${floorPlanId}/pins`
    );
    dispatch(slice.actions.setPins({ id: floorPlanId, pins }));
  };

export const upsertPin =
  (floorPlanId: number, assetId: number, x: number, y: number): AppThunk =>
  async (dispatch, getState) => {
    const existed = (
      getState().floorPlans.pinsByFloorPlan[floorPlanId] ?? []
    ).some((p) => p.asset.id === assetId);
    // PUT: the shared api client has no put helper, reuse get() with options
    const pin = await api.get<FloorPlanPin>(
      `${basePath}/${floorPlanId}/pins/${assetId}`,
      { method: 'PUT', body: JSON.stringify({ x, y }) }
    );
    dispatch(slice.actions.upsertPin({ id: floorPlanId, pin }));
    if (!existed) {
      dispatch(slice.actions.adjustPinCount({ id: floorPlanId, delta: 1 }));
    }
  };

export const deletePin =
  (floorPlanId: number, assetId: number): AppThunk =>
  async (dispatch) => {
    const response = await api.deletes<{ success: boolean }>(
      `${basePath}/${floorPlanId}/pins/${assetId}`
    );
    if (response.success) {
      dispatch(slice.actions.removePin({ id: floorPlanId, assetId }));
      dispatch(slice.actions.adjustPinCount({ id: floorPlanId, delta: -1 }));
    }
  };

export const getPinnableAssets =
  (floorPlanId: number, search?: string): AppThunk =>
  async () => {
    return api.get<PinnableAsset[]>(
      `${basePath}/${floorPlanId}/pinnable-assets?search=${encodeURIComponent(
        search ?? ''
      )}`
    );
  };

export const getAssetFloorPlanPins =
  (assetId: number): AppThunk =>
  async () => {
    return api.get<AssetFloorPlanPin[]>(`assets/${assetId}/floor-plan-pins`);
  };

export default slice;

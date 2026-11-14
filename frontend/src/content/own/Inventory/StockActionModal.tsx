import {
  Autocomplete,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  debounce,
  Typography
} from '@mui/material';
import { useContext, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from '../../../store';
import {
  countStock,
  issueStock,
  receiveStock
} from '../../../slices/part';
import { getWorkOrdersMini } from '../../../slices/workOrder';
import { CustomSnackBarContext } from '../../../contexts/CustomSnackBarContext';
import { getErrorMessage } from '../../../utils/api';
import Part from '../../../models/owns/part';
import { SearchCriteria } from '../../../models/owns/page';

export type StockActionMode = 'receive' | 'issue' | 'count';

interface StockActionModalProps {
  open: boolean;
  onClose: () => void;
  part: Part;
  mode: StockActionMode;
}

interface WoOption {
  id: number;
  title: string;
}

export default function StockActionModal({
  open,
  onClose,
  part,
  mode
}: StockActionModalProps) {
  const { t }: { t: any } = useTranslation();
  const { showSnackBar } = useContext(CustomSnackBarContext);
  const dispatch = useDispatch();
  const { workOrdersMini } = useSelector((state) => state.workOrders);
  const [quantity, setQuantity] = useState<string>('');
  const [unitCost, setUnitCost] = useState<string>('');
  const [counted, setCounted] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [workOrder, setWorkOrder] = useState<WoOption | null>(null);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [sending, setSending] = useState<boolean>(false);
  const onHand = part?.quantity ?? 0;

  useEffect(() => {
    if (open) {
      setQuantity('');
      setUnitCost(part?.cost != null ? String(part.cost) : '');
      setCounted('');
      setReason('');
      setWorkOrder(null);
      setSubmitted(false);
    }
  }, [open, mode, part?.id]);

  const searchWorkOrders = (query: string) => {
    const criteria: SearchCriteria = {
      filterFields: query
        ? [
            {
              field: 'title',
              value: query,
              operation: 'cn',
              alternatives: [{ field: 'customId', value: query, operation: 'cn' }]
            }
          ]
        : [],
      pageSize: 10,
      pageNum: 0,
      direction: 'DESC'
    };
    dispatch(getWorkOrdersMini(criteria));
  };
  const debouncedSearch = useMemo(() => debounce(searchWorkOrders, 500), []);
  useEffect(() => {
    if (open && mode === 'issue') searchWorkOrders('');
  }, [open, mode]);
  useEffect(() => () => (debouncedSearch as any).clear(), []);

  const qtyNum = Number(quantity);
  const countedNum = Number(counted);
  const variance = counted === '' ? null : countedNum - onHand;

  let quantityError = '';
  if (mode !== 'count') {
    if (quantity === '' || !(qtyNum > 0)) {
      quantityError = t('quantity_must_be_positive');
    } else if (mode === 'issue' && qtyNum > onHand) {
      quantityError = t('quantity_exceeds_on_hand');
    }
  }
  let countedError = '';
  if (mode === 'count' && (counted === '' || !(countedNum >= 0))) {
    countedError = t('counted_must_be_zero_or_more');
  }
  let reasonError = '';
  if (mode === 'issue' && !workOrder && !reason.trim()) {
    reasonError = t('reason_required_without_work_order');
  } else if (mode === 'count' && variance !== null && variance !== 0 && !reason.trim()) {
    reasonError = t('reason_required_when_variance');
  }
  const hasError = Boolean(quantityError || countedError || reasonError);

  const handleSubmit = async () => {
    setSubmitted(true);
    if (hasError) return;
    setSending(true);
    try {
      if (mode === 'receive') {
        await dispatch(
          receiveStock(part.id, {
            quantity: qtyNum,
            reason: reason.trim() || undefined,
            unitCost: unitCost === '' ? undefined : Number(unitCost)
          })
        );
      } else if (mode === 'issue') {
        await dispatch(
          issueStock(part.id, {
            quantity: qtyNum,
            workOrderId: workOrder?.id,
            reason: reason.trim() || undefined
          })
        );
      } else {
        await dispatch(
          countStock(part.id, {
            counted: countedNum,
            reason: reason.trim() || undefined
          })
        );
      }
      showSnackBar(t('operation_success'), 'success');
      onClose();
    } catch (err) {
      showSnackBar(getErrorMessage(err), 'error');
    } finally {
      setSending(false);
    }
  };

  const titles = {
    receive: t('receive_stock'),
    issue: t('issue_stock'),
    count: t('count_stock')
  };

  return (
    <Dialog fullWidth maxWidth="sm" open={open} onClose={sending ? undefined : onClose}>
      <DialogTitle sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          {titles[mode]}
        </Typography>
        <Typography variant="subtitle2">
          {part?.name} · {t('on_hand')}: {onHand}
          {part?.unit ? ` ${part.unit}` : ''}
        </Typography>
      </DialogTitle>
      <DialogContent dividers sx={{ p: 3 }}>
        <Box display="flex" flexDirection="column" gap={2}>
          {mode !== 'count' && (
            <TextField
              type="number"
              label={t('quantity')}
              value={quantity}
              required
              fullWidth
              inputProps={{ min: 0, step: 'any' }}
              onChange={(e) => setQuantity(e.target.value)}
              error={submitted && !!quantityError}
              helperText={
                submitted && quantityError
                  ? quantityError
                  : mode === 'issue'
                  ? `${t('on_hand')}: ${onHand}`
                  : ''
              }
            />
          )}
          {mode === 'receive' && (
            <TextField
              type="number"
              label={t('unit_cost')}
              value={unitCost}
              fullWidth
              inputProps={{ min: 0, step: 'any' }}
              onChange={(e) => setUnitCost(e.target.value)}
            />
          )}
          {mode === 'issue' && (
            <Autocomplete<WoOption, false, false, false>
              options={workOrdersMini.content as WoOption[]}
              value={workOrder}
              getOptionLabel={(o) => o.title}
              isOptionEqualToValue={(a, b) => a.id === b.id}
              filterOptions={(x) => x}
              onChange={(_e, v) => setWorkOrder(v)}
              onInputChange={(_e, v, reasonType) => {
                if (reasonType === 'input') debouncedSearch(v);
              }}
              renderInput={(params) => (
                <TextField {...params} label={t('work_order')} />
              )}
            />
          )}
          {mode === 'count' && (
            <>
              <TextField
                label={t('book_quantity')}
                value={onHand}
                fullWidth
                disabled
              />
              <TextField
                type="number"
                label={t('counted_quantity')}
                value={counted}
                required
                fullWidth
                inputProps={{ min: 0, step: 'any' }}
                onChange={(e) => setCounted(e.target.value)}
                error={submitted && !!countedError}
                helperText={submitted ? countedError : ''}
              />
              {variance !== null && (
                <Typography
                  variant="h5"
                  sx={{
                    color:
                      variance > 0
                        ? 'success.main'
                        : variance < 0
                        ? 'error.main'
                        : 'text.secondary'
                  }}
                >
                  {t('variance')}: {variance > 0 ? '+' : variance < 0 ? '−' : ''}
                  {Math.abs(variance)}
                </Typography>
              )}
            </>
          )}
          <TextField
            label={t('reason')}
            placeholder={mode === 'receive' ? t('delivery_note_supplier') : ''}
            value={reason}
            multiline
            minRows={2}
            fullWidth
            required={mode !== 'receive'}
            onChange={(e) => setReason(e.target.value)}
            error={submitted && !!reasonError}
            helperText={submitted ? reasonError : ''}
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={sending}>
          {t('cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={sending}
          startIcon={sending ? <CircularProgress size="1rem" /> : null}
        >
          {titles[mode]}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

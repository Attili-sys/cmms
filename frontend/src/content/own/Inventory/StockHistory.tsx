import {
  Box,
  Chip,
  CircularProgress,
  Link,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography
} from '@mui/material';
import { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Part from '../../../models/owns/part';
import { MovementType } from '../../../models/owns/stockMovement';
import { CompanySettingsContext } from '../../../contexts/CompanySettingsContext';
import { useDispatch, useSelector } from '../../../store';
import { getStockMovements } from '../../../slices/part';
import { getPurchaseOrderUrl, getWorkOrderUrl } from '../../../utils/urlPaths';

const chipColor = (
  type: MovementType
): 'success' | 'error' | 'warning' | 'info' | 'default' => {
  switch (type) {
    case 'RECEIPT':
    case 'PO_RECEIPT':
    case 'WO_RETURN':
      return 'success';
    case 'ISSUE':
    case 'WO_CONSUMPTION':
      return 'error';
    case 'PO_REVERSAL':
      return 'warning';
    case 'COUNT_GAIN':
    case 'COUNT_LOSS':
      return 'info';
    default:
      return 'default';
  }
};

export default function StockHistory({ part }: { part: Part }) {
  const { t }: { t: any } = useTranslation();
  const dispatch = useDispatch();
  const { getFormattedDate } = useContext(CompanySettingsContext);
  const movements = useSelector((state) => state.parts.movementsByPart[part.id]);
  const [page, setPage] = useState<number>(0);
  const [size, setSize] = useState<number>(20);
  const [loading, setLoading] = useState<boolean>(false);
  // Any stock action changes the part quantity (or at least returns a new part
  // object): jump back to page 0 so the newest movement is visible.
  useEffect(() => {
    setPage(0);
  }, [part.quantity, part.updatedAt]);

  useEffect(() => {
    setLoading(true);
    dispatch(getStockMovements(part.id, page, size))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [part.id, page, size, part.quantity, part.updatedAt]);

  const formatChange = (c: number) => (c > 0 ? `+${c}` : c < 0 ? `−${Math.abs(c)}` : '0');

  return (
    <Box>
      {loading && !movements ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : !movements?.content.length ? (
        <Stack direction="row" justifyContent="center" width="100%">
          <Typography variant="h5">{t('no_stock_movements')}</Typography>
        </Stack>
      ) : (
        <>
          <TableContainer sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('when')}</TableCell>
                  <TableCell>{t('movement')}</TableCell>
                  <TableCell align="right">{t('change')}</TableCell>
                  <TableCell align="right">{t('balance')}</TableCell>
                  <TableCell>{t('by')}</TableCell>
                  <TableCell>{t('reference')}</TableCell>
                  <TableCell>{t('reason')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {movements.content.map((m) => (
                  <TableRow key={m.id} hover>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      {getFormattedDate(m.createdAt)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={chipColor(m.movementType)}
                        label={t(`movement_${m.movementType}`)}
                      />
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{
                        fontWeight: 'bold',
                        color:
                          m.change > 0
                            ? 'success.main'
                            : m.change < 0
                            ? 'error.main'
                            : 'text.secondary'
                      }}
                    >
                      {formatChange(m.change)}
                    </TableCell>
                    <TableCell align="right">
                      {m.balanceAfter ?? '—'}
                    </TableCell>
                    <TableCell>
                      {m.createdBy
                        ? `${m.createdBy.firstName} ${m.createdBy.lastName}`
                        : '—'}
                    </TableCell>
                    <TableCell>
                      <Stack>
                        {m.workOrder && (
                          <Link
                            component={RouterLink}
                            to={getWorkOrderUrl(m.workOrder.id)}
                          >
                            {m.workOrder.customId || m.workOrder.title}
                          </Link>
                        )}
                        {m.purchaseOrder && (
                          <Link
                            component={RouterLink}
                            to={getPurchaseOrderUrl(m.purchaseOrder.id)}
                          >
                            {m.purchaseOrder.name}
                          </Link>
                        )}
                        {!m.workOrder && !m.purchaseOrder && '—'}
                      </Stack>
                    </TableCell>
                    <TableCell sx={{ minWidth: 160 }}>{m.reason || '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={movements.totalElements}
            page={page}
            rowsPerPage={size}
            rowsPerPageOptions={[10, 20, 50]}
            onPageChange={(_e, p) => setPage(p)}
            onRowsPerPageChange={(e) => {
              setSize(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </>
      )}
    </Box>
  );
}

import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { CheckCircle, Plus, Trash2, FileText, Download } from 'lucide-react';
import api from '@/api/client';
import { useToast } from '@/components/ui/Toast';

export function MaintenanceDetailsModal({ open, onClose, recordId, onComplete }) {
  const { success, error } = useToast();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(false);

  // Form states
  const [partName, setPartName] = useState('');
  const [partQuantity, setPartQuantity] = useState(1);
  const [partCost, setPartCost] = useState(0);

  const [labourDesc, setLabourDesc] = useState('');
  const [labourHours, setLabourHours] = useState(1);
  const [labourRate, setLabourRate] = useState(0);

  const [file, setFile] = useState(null);

  useEffect(() => {
    if (open && recordId) {
      loadRecord();
    }
  }, [open, recordId]);

  const loadRecord = async () => {
    setLoading(true);
    try {
      const res = await api.maintenance.get(recordId);
      setRecord(res);
    } catch (e) {
      error('Error', 'Failed to load maintenance details');
    } finally {
      setLoading(false);
    }
  };

  const isEditable = record?.status === 'SCHEDULED' || record?.status === 'IN_PROGRESS' || record?.status === 'CREATED';

  const handleAddPart = async () => {
    if (!partName || partQuantity <= 0 || partCost < 0) return;
    try {
      await api.maintenance.addPart(recordId, {
        name: partName,
        quantity: Number(partQuantity),
        unit_cost: Number(partCost)
      });
      setPartName('');
      setPartQuantity(1);
      setPartCost(0);
      loadRecord();
      success('Success', 'Part added');
    } catch (e) {
      error('Error', 'Failed to add part');
    }
  };

  const handleRemovePart = async (partId) => {
    try {
      await api.maintenance.removePart(recordId, partId);
      loadRecord();
    } catch (e) {
      error('Error', 'Failed to remove part');
    }
  };

  const handleAddLabour = async () => {
    if (!labourDesc || labourHours <= 0 || labourRate < 0) return;
    try {
      await api.maintenance.addLabour(recordId, {
        description: labourDesc,
        hours: Number(labourHours),
        hourly_rate: Number(labourRate)
      });
      setLabourDesc('');
      setLabourHours(1);
      setLabourRate(0);
      loadRecord();
      success('Success', 'Labour added');
    } catch (e) {
      error('Error', 'Failed to add labour');
    }
  };

  const handleRemoveLabour = async (labourId) => {
    try {
      await api.maintenance.removeLabour(recordId, labourId);
      loadRecord();
    } catch (e) {
      error('Error', 'Failed to remove labour');
    }
  };

  const handleUploadDocument = async () => {
    if (!file) return;
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const docRes = await api.documents.upload(formData);
      await api.maintenance.addDocument(recordId, { document_id: docRes.id });
      setFile(null);
      loadRecord();
      success('Success', 'Document uploaded');
    } catch (e) {
      error('Error', 'Failed to upload document');
    }
  };

  if (!record) return null;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Maintenance Ticket Details"
      closable
      size="lg"
      footer={
        record.status === 'SCHEDULED' && (
          <Button
            variant="success"
            icon={<CheckCircle className="h-4 w-4" />}
            onClick={() => onComplete(record.id)}
          >
            Mark Completed
          </Button>
        )
      }
    >
      <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
        <div className="flex justify-between items-start border-b border-border pb-3">
          <div>
            <h4 className="font-bold text-content text-lg">{record.business_id}</h4>
            <p className="text-xs text-content-secondary">{record.category}</p>
          </div>
          <Badge variant={record.status === 'COMPLETED' ? 'success' : 'warning'}>
            {record.status}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-content-secondary">Odometer:</span> <span className="font-medium">{record.odometer} km</span></div>
          <div><span className="text-content-secondary">Workshop:</span> <span className="font-medium">{record.workshop}</span></div>
          <div className="col-span-2 pt-2 border-t border-border mt-2">
            <span className="text-xs text-content-secondary block uppercase font-semibold">Description</span>
            <p className="text-xs text-content mt-1 italic">{record.description}</p>
          </div>
        </div>

        {/* Parts Section */}
        <div className="border border-border rounded-lg p-4">
          <h5 className="font-bold mb-3 flex items-center justify-between">
            Parts
          </h5>
          <table className="w-full text-sm text-left mb-4">
            <thead>
              <tr className="border-b border-border text-content-secondary">
                <th className="py-2">Part</th>
                <th className="py-2">Qty</th>
                <th className="py-2">Unit Cost</th>
                <th className="py-2">Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {record.parts?.map(p => (
                <tr key={p.id} className="border-b border-border">
                  <td className="py-2">{p.name}</td>
                  <td className="py-2">{p.quantity}</td>
                  <td className="py-2">₹{p.unit_cost.toLocaleString()}</td>
                  <td className="py-2 font-bold">₹{p.total_cost.toLocaleString()}</td>
                  <td className="py-2 text-right">
                    {isEditable && (
                      <Button variant="ghost" size="sm" onClick={() => handleRemovePart(p.id)} icon={<Trash2 className="h-4 w-4 text-red-500" />} />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {isEditable && (
            <div className="flex gap-2 items-end">
              <Input label="Name" value={partName} onChange={e => setPartName(e.target.value)} />
              <Input label="Qty" type="number" value={partQuantity} onChange={e => setPartQuantity(e.target.value)} />
              <Input label="Unit Cost" type="number" value={partCost} onChange={e => setPartCost(e.target.value)} />
              <Button onClick={handleAddPart} variant="outline" size="sm" icon={<Plus className="h-4 w-4"/>}>Add</Button>
            </div>
          )}
        </div>

        {/* Labour Section */}
        <div className="border border-border rounded-lg p-4">
          <h5 className="font-bold mb-3">Labour</h5>
          <table className="w-full text-sm text-left mb-4">
            <thead>
              <tr className="border-b border-border text-content-secondary">
                <th className="py-2">Description</th>
                <th className="py-2">Hours</th>
                <th className="py-2">Rate/hr</th>
                <th className="py-2">Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {record.labour?.map(l => (
                <tr key={l.id} className="border-b border-border">
                  <td className="py-2">{l.description}</td>
                  <td className="py-2">{l.hours}</td>
                  <td className="py-2">₹{l.hourly_rate.toLocaleString()}</td>
                  <td className="py-2 font-bold">₹{l.total_cost.toLocaleString()}</td>
                  <td className="py-2 text-right">
                    {isEditable && (
                      <Button variant="ghost" size="sm" onClick={() => handleRemoveLabour(l.id)} icon={<Trash2 className="h-4 w-4 text-red-500" />} />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {isEditable && (
            <div className="flex gap-2 items-end">
              <Input label="Description" value={labourDesc} onChange={e => setLabourDesc(e.target.value)} />
              <Input label="Hours" type="number" value={labourHours} onChange={e => setLabourHours(e.target.value)} />
              <Input label="Rate" type="number" value={labourRate} onChange={e => setLabourRate(e.target.value)} />
              <Button onClick={handleAddLabour} variant="outline" size="sm" icon={<Plus className="h-4 w-4"/>}>Add</Button>
            </div>
          )}
        </div>

        {/* Cost Breakdown */}
        <div className="bg-brand-50 p-4 rounded-lg">
          <h5 className="font-bold text-brand-700 mb-2">Cost Breakdown</h5>
          <div className="flex justify-between text-sm text-brand-600 mb-1">
            <span>Parts Total:</span>
            <span>₹{(record.parts?.reduce((sum, p) => sum + p.total_cost, 0) || 0).toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm text-brand-600 mb-1">
            <span>Labour Total:</span>
            <span>₹{(record.labour?.reduce((sum, l) => sum + l.total_cost, 0) || 0).toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm text-brand-600 mb-2 pb-2 border-b border-brand-200">
            <span>Other Cost:</span>
            <span>₹{(record.other_cost || 0).toLocaleString()}</span>
          </div>
          <div className="flex justify-between font-bold text-lg text-brand-800">
            <span>Maintenance Total Cost:</span>
            <span>₹{(record.cost || 0).toLocaleString()}</span>
          </div>
        </div>

        {/* Documents */}
        <div className="border border-border rounded-lg p-4">
          <h5 className="font-bold mb-3 flex items-center gap-2"><FileText className="h-4 w-4" /> Receipts & Documents</h5>
          {record.documents?.length > 0 ? (
            <ul className="space-y-2 mb-4">
              {record.documents.map(d => (
                <li key={d.id} className="flex items-center justify-between p-2 bg-background rounded border border-border">
                  <span className="text-sm font-medium">{d.document_id}</span>
                  <a href={`/api/v1/documents/${d.document_id}/download`} target="_blank" rel="noreferrer">
                    <Button variant="ghost" size="sm" icon={<Download className="h-4 w-4" />} />
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-content-secondary mb-4">No documents uploaded.</p>
          )}

          <div className="flex gap-2">
            <input type="file" onChange={e => setFile(e.target.files[0])} className="text-sm" />
            <Button onClick={handleUploadDocument} variant="outline" size="sm" disabled={!file}>Upload</Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}

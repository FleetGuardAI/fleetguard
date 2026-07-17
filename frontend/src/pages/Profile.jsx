import React, { useState, useEffect } from 'react';
import { Shield, Building2, User, Phone, Mail, Save } from 'lucide-react';
import { getStoredUser, updateCompany } from '@/api/authApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { Loader } from '@/components/ui/Loader';

export default function Profile() {
  const { success, error } = useToast();
  
  const [companyName, setCompanyName] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [email, setEmail] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    const fetchUserProfile = () => {
      setFetching(true);
      try {
        const u = getStoredUser();
        if (u) {
          setCompanyName(u.company?.company_name || '');
          setOwnerName(u.name || '');
          setMobileNumber(u.mobile_number || '');
          setEmail(u.email || '');
        }
      } catch (e) {
        error('Load Failed', 'Could not load company profile.');
      } finally {
        setFetching(false);
      }
    };
    fetchUserProfile();
  }, []);

  const validate = () => {
    const errs = {};
    if (!companyName.trim()) errs.companyName = 'Company name is required';
    if (!ownerName.trim()) errs.ownerName = 'Owner / Admin name is required';
    
    if (!mobileNumber.trim()) {
      errs.mobileNumber = 'Mobile number is required';
    } else if (!/^\+?[1-9]\d{9,14}$/.test(mobileNumber.trim())) {
      errs.mobileNumber = 'Use a valid number (e.g. +919876543210)';
    }

    if (email && !/^\S+@\S+\.\S+$/.test(email.trim())) {
      errs.email = 'Invalid email address';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const payload = {
      company_name: companyName.trim(),
      owner_name: ownerName.trim(),
      mobile_number: mobileNumber.trim(),
      email: email.trim() || null,
    };

    try {
      await updateCompany(payload);
      success('Profile Updated', 'Company details successfully updated.');
      
      // Dispatch an event so that top navbar and sidebar update user name automatically
      window.dispatchEvent(new Event('storage'));
    } catch (e) {
      error('Update Failed', e.message || 'An error occurred while saving.');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-content">Company Profile Settings</h1>
        <p className="text-sm text-content-secondary mt-0.5">
          View and manage details of your transport company tenant account.
        </p>
      </div>

      <Card>
        <div className="flex items-center gap-4 pb-6 mb-6 border-b border-border">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Building2 className="h-7 w-7 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-content">{companyName || 'Company Account'}</h3>
            <p className="text-xs text-content-muted uppercase tracking-wider font-semibold">Admin Settings Panel</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Company Name"
            placeholder="e.g. RoutePay Logistics Pvt Ltd"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            error={errors.companyName}
            icon={<Building2 className="h-4 w-4" />}
            required
          />

          <Input
            label="Owner / Primary Admin Name"
            placeholder="e.g. Suryansh Chaudhary"
            value={ownerName}
            onChange={(e) => setOwnerName(e.target.value)}
            error={errors.ownerName}
            icon={<User className="h-4 w-4" />}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Contact Mobile Number"
              placeholder="e.g. +919876543210"
              value={mobileNumber}
              onChange={(e) => setMobileNumber(e.target.value)}
              error={errors.mobileNumber}
              icon={<Phone className="h-4 w-4" />}
              required
            />
            <Input
              label="Company Email Address"
              placeholder="e.g. admin@routepay.com"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              icon={<Mail className="h-4 w-4" />}
            />
          </div>

          <div className="flex justify-end gap-3 pt-6 border-t border-border">
            <Button
              type="submit"
              variant="primary"
              icon={<Save className="h-4 w-4" />}
              loading={loading}
            >
              Save Profile Changes
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

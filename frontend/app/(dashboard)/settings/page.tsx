'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, Loader2, User, Lock, Building } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Header from '@/components/layout/Header';
import { useAuthStore } from '@/store/auth';

const profileSchema = z.object({
  name: z.string().min(2, 'Name is required'),
  email: z.string().email('Invalid email'),
  organization_name: z.string().min(2, 'Organization is required'),
});

const passwordSchema = z
  .object({
    current_password: z.string().min(6),
    new_password: z.string().min(8),
    confirm_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  });

export default function SettingsPage() {
  const { user } = useAuthStore();

  const profileForm = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name || '',
      email: user?.email || '',
      organization_name: user?.organization_name || '',
    },
  });

  const passwordForm = useForm({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header title="Settings" subtitle="Manage your account and preferences" />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Profile */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-5">
              <User className="w-5 h-5 text-gray-400" />
              <h2 className="font-semibold text-gray-900">Profile Information</h2>
            </div>

            <form className="space-y-4">
              <div className="flex items-center gap-4 mb-5">
                <div className="w-16 h-16 rounded-full bg-indigo-100 text-indigo-700 font-bold text-xl flex items-center justify-center">
                  {user?.name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{user?.name}</p>
                  <p className="text-sm text-gray-500 capitalize">{user?.role}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input {...profileForm.register('name')} />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input type="email" {...profileForm.register('email')} />
                </div>
              </div>

              <div className="space-y-2">
                <Label>
                  <Building className="w-4 h-4 inline mr-1" />
                  Organization Name
                </Label>
                <Input {...profileForm.register('organization_name')} />
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" className="gap-2">
                  <Save className="w-4 h-4" />
                  Save Profile
                </Button>
              </div>
            </form>
          </div>

          {/* Password */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-5">
              <Lock className="w-5 h-5 text-gray-400" />
              <h2 className="font-semibold text-gray-900">Change Password</h2>
            </div>

            <form className="space-y-4">
              <div className="space-y-2">
                <Label>Current Password</Label>
                <Input type="password" {...passwordForm.register('current_password')} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>New Password</Label>
                  <Input type="password" {...passwordForm.register('new_password')} />
                </div>
                <div className="space-y-2">
                  <Label>Confirm New Password</Label>
                  <Input type="password" {...passwordForm.register('confirm_password')} />
                </div>
              </div>
              <div className="flex justify-end pt-2">
                <Button type="submit" className="gap-2">
                  <Lock className="w-4 h-4" />
                  Update Password
                </Button>
              </div>
            </form>
          </div>

          {/* Danger zone */}
          <div className="bg-white rounded-xl border border-red-200 p-6">
            <h2 className="font-semibold text-red-700 mb-2">Danger Zone</h2>
            <p className="text-sm text-gray-500 mb-4">
              Once you delete your account, all data will be permanently removed.
            </p>
            <Button variant="destructive" size="sm">Delete Account</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

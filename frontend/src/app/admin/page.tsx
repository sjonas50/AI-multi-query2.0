"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { User, InviteCode } from "@/lib/types";

export default function AdminPage() {
  const { user, isAdmin } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [invites, setInvites] = useState<InviteCode[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [newCode, setNewCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAdmin) {
      router.push("/");
      return;
    }
    refresh();
  }, [isAdmin, router]);

  const refresh = useCallback(() => {
    api.get<{ items: User[] }>("/api/admin/users").then((r) => setUsers(r.items));
    api.get<{ items: InviteCode[] }>("/api/admin/invites").then((r) => setInvites(r.items));
  }, []);

  const handleCreateInvite = async () => {
    setLoading(true);
    try {
      const res = await api.post<{ code: string }>("/api/admin/invites", {
        email: inviteEmail || null,
        expires_hours: 72,
      });
      setNewCode(res.code);
      setInviteEmail("");
      refresh();
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeInvite = async (code: string) => {
    await api.delete(`/api/admin/invites/${code}`);
    refresh();
  };

  const handleRemoveUser = async (userId: string) => {
    if (!confirm("Remove this user? This cannot be undone.")) return;
    await api.delete(`/api/admin/users/${userId}`);
    refresh();
  };

  if (!isAdmin) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Admin</h2>

      {/* Generate Invite */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Generate Invite Code</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label htmlFor="inviteEmail">Lock to email (optional)</Label>
            <Input
              id="inviteEmail"
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="user@example.com"
              className="mt-1 max-w-xs"
            />
          </div>
          <Button onClick={handleCreateInvite} disabled={loading}>
            {loading ? "Generating..." : "Generate Invite"}
          </Button>
          {newCode && (
            <div className="rounded-md border border-green-300 bg-green-50 p-3 text-sm dark:border-green-800 dark:bg-green-950">
              <p className="font-medium text-green-800 dark:text-green-200">Invite code created:</p>
              <code className="mt-1 block text-lg font-mono text-green-900 dark:text-green-100">
                {newCode}
              </code>
              <p className="mt-1 text-xs text-green-700 dark:text-green-300">
                Share this code with the person you want to invite. Expires in 72 hours.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Invite Codes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Invite Codes</CardTitle>
        </CardHeader>
        <CardContent>
          {invites.length === 0 ? (
            <p className="text-sm text-muted-foreground">No invite codes yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 pr-4 font-medium">Code</th>
                    <th className="pb-2 pr-4 font-medium">Locked To</th>
                    <th className="pb-2 pr-4 font-medium">Status</th>
                    <th className="pb-2 pr-4 font-medium">Expires</th>
                    <th className="pb-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {invites.map((inv) => (
                    <tr key={inv.code} className="border-b last:border-0">
                      <td className="py-2 pr-4 font-mono text-xs">{inv.code}</td>
                      <td className="py-2 pr-4">{inv.email || "—"}</td>
                      <td className="py-2 pr-4">
                        {inv.used_by ? (
                          <Badge variant="secondary">Used</Badge>
                        ) : inv.active ? (
                          <Badge variant="outline" className="border-green-500 text-green-700 dark:border-green-600 dark:text-green-400">Active</Badge>
                        ) : (
                          <Badge variant="destructive">Expired</Badge>
                        )}
                      </td>
                      <td className="py-2 pr-4 text-xs text-muted-foreground">
                        {new Date(inv.expires_at).toLocaleDateString()}
                      </td>
                      <td className="py-2">
                        {inv.active && !inv.used_by && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRevokeInvite(inv.code)}
                            className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          >
                            Revoke
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Users */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Users</CardTitle>
        </CardHeader>
        <CardContent>
          {users.length === 0 ? (
            <p className="text-sm text-muted-foreground">No users.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Email</th>
                    <th className="pb-2 pr-4 font-medium">Role</th>
                    <th className="pb-2 pr-4 font-medium">Joined</th>
                    <th className="pb-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b last:border-0">
                      <td className="py-2 pr-4">{u.display_name}</td>
                      <td className="py-2 pr-4 text-muted-foreground">{u.email}</td>
                      <td className="py-2 pr-4">
                        <Badge variant={u.role === "admin" ? "default" : "outline"}>
                          {u.role}
                        </Badge>
                      </td>
                      <td className="py-2 pr-4 text-xs text-muted-foreground">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-2">
                        {u.id !== user?.id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveUser(u.id)}
                            className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          >
                            Remove
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { Plus, Key, Copy, Trash2, AlertCircle, Clock, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import type { APIKey, APIKeyCreate, APIKeyCreated, APIKeyType } from '@/lib/types/api-keys';

export function APIKeysSection() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showKeyDialog, setShowKeyDialog] = useState(false);
  const [createdKey, setCreatedKey] = useState<APIKeyCreated | null>(null);
  const [keySaved, setKeySaved] = useState(false);

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      const apiKey = localStorage.getItem('cortexdb_api_key');
      const res = await fetch('http://localhost:8000/api-keys', {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setKeys(data);
      }
    } catch (error) {
      console.error('Failed to fetch keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (data: APIKeyCreate) => {
    try {
      const apiKey = localStorage.getItem('cortexdb_api_key');
      const res = await fetch('http://localhost:8000/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        const newKey = await res.json();
        setCreatedKey(newKey);
        setShowCreateDialog(false);
        setShowKeyDialog(true);
        setKeySaved(false);
        await fetchKeys();
      }
    } catch (error) {
      console.error('Failed to create key:', error);
    }
  };

  const handleDeleteKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key?')) return;

    try {
      const apiKey = localStorage.getItem('cortexdb_api_key');
      const res = await fetch(`http://localhost:8000/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });

      if (res.ok) {
        await fetchKeys();
      }
    } catch (error) {
      console.error('Failed to delete key:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getTypeColor = (type: APIKeyType) => {
    switch (type) {
      case 'admin':
        return 'bg-red-500';
      case 'database':
        return 'bg-blue-500';
      case 'readonly':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getTypeIcon = (type: APIKeyType) => {
    switch (type) {
      case 'admin':
        return <Shield className="w-4 h-4" />;
      case 'database':
        return <Key className="w-4 h-4" />;
      case 'readonly':
        return <Clock className="w-4 h-4" />;
      default:
        return <Key className="w-4 h-4" />;
    }
  };

  const formatDate = (date?: string) => {
    if (!date) return 'Never';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>API Keys</span>
            <Button onClick={() => setShowCreateDialog(true)} size="sm">
              <Plus className="w-4 h-4 mr-2" />
              New Key
            </Button>
          </CardTitle>
          <CardDescription>
            Manage API keys for authentication and authorization
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : keys.length === 0 ? (
            <div className="text-center py-8">
              <Key className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No API keys yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first API key to start using CortexDB
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create API Key
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {keys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-start justify-between rounded-lg border border-border/70 bg-secondary/20 p-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`p-2 rounded ${getTypeColor(key.type)}`}>
                        {getTypeIcon(key.type)}
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold">{key.name}</h3>
                        <p className="text-xs text-muted-foreground">{key.description}</p>
                      </div>
                      <Badge variant={key.enabled ? 'default' : 'secondary'} className="text-xs">
                        {key.type}
                      </Badge>
                    </div>

                    <div className="mt-2 space-y-1 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Key:</span>
                        <code className="bg-secondary px-2 py-1 rounded font-mono text-xs">
                          {key.key_prefix}
                        </code>
                        <span className="text-muted-foreground text-xs">
                          (prefix only - full key shown only when created)
                        </span>
                      </div>

                      {key.permissions.databases.length > 0 && (
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">Databases:</span>
                          <span>{key.permissions.databases.join(', ')}</span>
                        </div>
                      )}

                      <div className="flex items-center gap-4 text-muted-foreground">
                        <span>Created: {formatDate(key.created_at)}</span>
                        {key.last_used_at && (
                          <span>Last used: {formatDate(key.last_used_at)}</span>
                        )}
                        {key.expires_at && (
                          <span>Expires: {formatDate(key.expires_at)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteKey(key.id)}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 w-8 p-0"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <CreateKeyDialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onCreate={handleCreateKey}
      />

      <ShowKeyDialog
        open={showKeyDialog}
        onClose={() => {
          setShowKeyDialog(false);
          setCreatedKey(null);
        }}
        apiKey={createdKey}
        keySaved={keySaved}
        onKeySaved={() => setKeySaved(true)}
      />
    </>
  );
}

function CreateKeyDialog({
  open,
  onClose,
  onCreate,
}: {
  open: boolean;
  onClose: () => void;
  onCreate: (data: APIKeyCreate) => void;
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<APIKeyType>('database');
  const [databases, setDatabases] = useState('default');

  const handleSubmit = () => {
    onCreate({
      name,
      description: description || undefined,
      type,
      databases: type === 'database' || type === 'readonly' ? databases.split(',').map(d => d.trim()) : undefined,
    });
    setName('');
    setDescription('');
    setType('database');
    setDatabases('default');
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create New API Key</DialogTitle>
          <DialogDescription>
            Create a new API key for accessing CortexDB
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Production Backend"
            />
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Used by production backend services"
              rows={2}
            />
          </div>

          <div>
            <Label htmlFor="type">Type *</Label>
            <select
              id="type"
              value={type}
              onChange={(e) => setType(e.target.value as APIKeyType)}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="database">Database - Specific databases access</option>
              <option value="readonly">Read-Only - Read and search only</option>
              <option value="admin">Admin - Full access + Dashboard</option>
            </select>
          </div>

          {(type === 'database' || type === 'readonly') && (
            <div>
              <Label htmlFor="databases">Databases (comma-separated)</Label>
              <Input
                id="databases"
                value={databases}
                onChange={(e) => setDatabases(e.target.value)}
                placeholder="default, analytics"
              />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name}>
            Create Key
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ShowKeyDialog({
  open,
  onClose,
  apiKey,
  keySaved,
  onKeySaved,
}: {
  open: boolean;
  onClose: () => void;
  apiKey: APIKeyCreated | null;
  keySaved: boolean;
  onKeySaved: () => void;
}) {
  if (!apiKey) return null;

  const connectionString = `cortexdb://${apiKey.key}@localhost:8000`;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600" />
            API Key Created Successfully
          </DialogTitle>
          <DialogDescription>
            Save this key now - you won&apos;t be able to see it again!
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label>API Key</Label>
            <div className="flex gap-2 mt-1">
              <code className="flex-1 bg-secondary px-4 py-3 rounded font-mono text-sm overflow-x-auto">
                {apiKey.key}
              </code>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(apiKey.key);
                }}
              >
                <Copy className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div>
            <Label>Connection String</Label>
            <div className="flex gap-2 mt-1">
              <code className="flex-1 bg-secondary px-4 py-3 rounded font-mono text-sm overflow-x-auto">
                {connectionString}
              </code>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(connectionString);
                }}
              >
                <Copy className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div className="text-sm">
                <p className="font-semibold text-yellow-900 mb-1">Important</p>
                <ul className="list-disc list-inside text-yellow-800 space-y-1">
                  <li>Save this key in a secure location</li>
                  <li>This is the only time you&apos;ll see the full key</li>
                  <li>Store it in your .env file or secrets manager</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            onClick={() => {
              onKeySaved();
              onClose();
            }}
            disabled={!keySaved}
          >
            ✓ I&apos;ve saved the key
          </Button>
          {!keySaved && (
            <Button variant="outline" onClick={onKeySaved}>
              Mark as saved
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { TrashIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface RemoveConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  videoTitle?: string;
  isLoading?: boolean;
}

export function RemoveConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  videoTitle,
  isLoading = false,
}: RemoveConfirmationModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Remove Video">
      <div className="flex flex-col items-center text-center py-4">
        {/* Warning Icon */}
        <div className="w-16 h-16 rounded-full bg-accent-red/10 flex items-center justify-center mb-4">
          <ExclamationTriangleIcon className="w-8 h-8 text-accent-red" />
        </div>

        {/* Message */}
        <p className="text-text-primary font-medium mb-2">
          Are you sure you want to remove this video?
        </p>
        {videoTitle && (
          <p className="text-text-secondary text-sm mb-4 line-clamp-2 px-4">
            "{videoTitle}"
          </p>
        )}
        <p className="text-text-tertiary text-xs">
          The video will be moved to Recently Deleted and can be restored within 30 days.
        </p>

        {/* Actions */}
        <div className="flex gap-3 mt-6 w-full">
          <Button
            variant="secondary"
            onClick={onClose}
            className="flex-1"
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={onConfirm}
            className="flex-1"
            isLoading={isLoading}
          >
            <TrashIcon className="w-4 h-4 mr-1.5" />
            Remove
          </Button>
        </div>
      </div>
    </Modal>
  );
}

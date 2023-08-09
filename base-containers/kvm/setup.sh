#! /bin/bash -x

# Load env variables
STUDENT_DIR=/task/student
KVM_DIR="${STUDENT_DIR}/kvm"
SCRIPTS_DIR="${STUDENT_DIR}/scripts"
STUDENT_LOGIN="${SCRIPTS_DIR}/student_login"

# Set kvm group in human-readable way
groupdel kvm
groupadd -g $(stat -c '%g' /dev/kvm) kvm

# Create RW dir mounted in the KVM
mkdir "${KVM_DIR}"
chown worker:worker /task
chown worker:worker "${KVM_DIR}"

# Copy the kernel in a path readable by "worker" within the SSH container
cp "${SCRIPTS_DIR}/bzImage" /tmp

# Copy student_login file, if any, in a path readable by "worker" within the VM
if [[ -f "${STUDENT_LOGIN}" ]]
then
    cp "${STUDENT_LOGIN}" /
fi

# Launch the KVM as "worker"
su - worker -G worker -G kvm -c "virtme-run --cpus 2 --memory 256 --kimg /tmp/bzImage --rwdir=/tmp/student=${KVM_DIR}"

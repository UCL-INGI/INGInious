#! /bin/bash -x

STUDENT_DIR=/task/student
KVM_DIR="${STUDENT_DIR}/kvm"

groupdel kvm
groupadd -g $(stat -c '%g' /dev/kvm) kvm
mkdir "${KVM_DIR}"
chown worker:worker "${KVM_DIR}"
cp "${STUDENT_DIR}/scripts/bzImage" /tmp
su - worker -G worker -G kvm -c "virtme-run --cpus 2 --memory 256 --kimg /tmp/bzImage --rwdir=/tmp/student=${KVM_DIR}"

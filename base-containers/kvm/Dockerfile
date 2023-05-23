ARG   	VERSION=latest
ARG	REGISTRY

# Rockylinux does not enable 9P virtfs in the shipped QEMU builds, hence we have to rebuild our own version
# Inspired from https://github.com/acudovs/qemu-kvm-virtfs/blob/master/rpmbuild/build
FROM rockylinux:8 as builder

# Enable additional repos
RUN 	dnf -y install 'dnf-command(config-manager)' &&\
   	dnf config-manager --set-enabled powertools

# Install dependencies to build QEMU
RUN 	yum -y update && yum -y install \
        glusterfs-api-devel \
        glusterfs-devel \
        iasl \
        libcacard-devel \
	libpmem-devel \
	nss-devel \
	pkgconfig \
	spice-protocol \
	spice-server-devel \
	usbredir-devel \
	yum-utils \
	'pkgconfig(epoxy)' \
	'pkgconfig(gbm)' \
	'pkgconfig(libdrm)'

# Apply patches and build QEMU
WORKDIR /opt
RUN 	yum-builddep -y qemu-kvm
RUN 	yumdownloader --source qemu-kvm
RUN 	rpm -Uvh qemu-kvm-*.src.rpm
RUN sed -i -e 's/--disable-virtfs/--enable-virtfs/' \
	-e 's/--disable-virtiofsd/--enable-virtiofsd/g' \
	/root/rpmbuild/SPECS/qemu-kvm.spec
RUN sed -i -e '/^%files -n qemu-kvm-common/,/^$/s/^$/%{_bindir}\/virtfs-proxy-helper\n%{_mandir}\/man1\/virtfs-proxy-helper.1.gz\n/' \
    -e '/^%if %{rhev}$/,/^%else$/s/pkgsuffix -ev/pkgsuffix -virtfs/' \
    -e '/%define rhel_rhev_conflicts()/ a Provides: %1-ev = %{epoch}:%{version}-%{release} \\\nObsoletes: %1-ev < %{obsoletes_version} \\' \
    -e 's/rm -rf ${RPM_BUILD_ROOT}%{_mandir}\/man1\/virtfs-proxy-helper\*//g' \
    -e 's/rm -rf ${RPM_BUILD_ROOT}%{_libexecdir}\/virtfs-proxy-helper/mv ${RPM_BUILD_ROOT}%{_libexecdir}\/virtfs-proxy-helper ${RPM_BUILD_ROOT}%{_bindir}\/virtfs-proxy-helper/g' \
    /root/rpmbuild/SPECS/qemu-kvm.spec
COPY 	virtio-9p-pci.patch /root/rpmbuild/SOURCES/
COPY 	qemu-kvm.spec.patch /tmp
RUN 	patch /root/rpmbuild/SPECS/qemu-kvm.spec /tmp/qemu-kvm.spec.patch
RUN 	rpmbuild -ba --clean /root/rpmbuild/SPECS/qemu-kvm.spec

# Build GNU telnetd server since classical builds do not allow running bash as login util
RUN	wget "https://ftp.gnu.org/gnu/inetutils/inetutils-2.4.tar.xz" &&\
	tar xf inetutils-2.4.tar.xz &&\
	cd inetutils-2.4 &&\
	./configure --disable-servers --disable-clients --enable-telnetd --enable-telnet &&\
	make -j$(nproc)

# =====================
# KVM base container
# =====================
FROM 	${REGISTRY}/inginious/env-base:${VERSION}

# Install QEMU with 9P virtifs enabled
COPY --from=builder /root/rpmbuild/RPMS/x86_64/qemu-*.rpm /tmp/
RUN 	yum localinstall -y /tmp/*rpm &&\
	rm -rf /tmp/*rpm &&\
	ln -s /usr/libexec/qemu-kvm /bin/qemu-kvm

# Install GNU telnet utils
COPY --from=builder /opt/inetutils-2.4/telnet/telnet /usr/sbin
COPY --from=builder /opt/inetutils-2.4/telnetd/telnetd /usr/sbin

# Install dependecies
RUN dnf install -y expect xinetd git

# Install virtme
WORKDIR /opt
COPY	virtme.patch .
RUN	git clone https://github.com/amluto/virtme &&\
	git -C virtme apply < virtme.patch &&\
	ln -s virtme/virtme-run /usr/sbin/virtme-run

# Get expect script launching the VM
COPY run.expect /

WORKDIR /

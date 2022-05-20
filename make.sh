#!/bin/bash

VERSION=`cat VERSION`
CODENAME=`cat CODENAME`

prep() {
	install -d dist
	rm -f dist/fchroot-$VERSION*
	cd man
	cd ..
	cat > fchroot/version.py << EOF
__version__ = "$VERSION"
__codename__ = "$CODENAME"
EOF
	for x in man/fchroot.1.rst setup.py; do
		sed -e "s/##VERSION##/$VERSION/g" \
		-e "s/##CODENAME##/$CODENAME/g" \
		${x}.in > ${x}
	done
	chmod 0755 bin/fchroot
	for x in man/*.rst; do
		cat $x | rst2man.py > ${x%.rst}
    done
}

commit() {
	git commit -a -m "$VERSION release."
	git tag -f "$VERSION"
	git push
	git push --tags
	python3 setup.py sdist
}

if [ "$1" = "prep" ]
then
	prep
elif [ "$1" = "commit" ]
then
	commit
elif [ "$1" = "all" ]
then
	prep
	commit
fi

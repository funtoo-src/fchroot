#!/bin/bash

VERSION=`cat VERSION`
CODENAME=`cat CODENAME`

prep() {
	install -d dist
	rm -f dist/fchroot-$VERSION*
	cd man
	for x in *.rst; do
	    cat $x | sed -e "s/##VERSION##/$VERSION/g" | rst2man.py > ${x%.rst}
    done
	cd ..
	sed -i -e "s/##VERSION##/$VERSION/g" \
	-e "s/##CODENAME##/$CODENAME/g" \
	bin/fchroot setup.py
}

commit() {
	cd doc
	git add *.[1-8]
	cd ..
	git commit -a -m "$VERSION distribution release"
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

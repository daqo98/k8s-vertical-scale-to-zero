REPO = quintero98
VERSCA20_IMAGE = proxy-vertical-scaling
VERSCA20_IMAGE_VERSION = $(VERSCA20_IMAGE):$(shell git tag --points-at HEAD)

release_versca20:
	@if [ -n "$(VERSCA20_IMAGE_VERSION)" ]; then \
		echo "Building $(VERSCA20_IMAGE_VERSION)" ;\
		docker build -t $(REPO)/$(VERSCA20_IMAGE_VERSION) -f Dockerfile_VerSca20.docker . ;\
		docker push $(REPO)/$(VERSCA20_IMAGE_VERSION) ;\
	else \
		echo "$(VERSCA20_IMAGE_VERSION) unchanged: no version tag on HEAD commit" ;\
	fi
release_versca20_threading:
	@if [ -n "$(VERSCA20_IMAGE_VERSION)" ]; then \
		echo "Building $(VERSCA20_IMAGE_VERSION)" ;\
		docker build -t $(REPO)/$(VERSCA20_IMAGE_VERSION) -f Dockerfile_VerSca20_threading.docker . ;\
		docker push $(REPO)/$(VERSCA20_IMAGE_VERSION) ;\
	else \
		echo "$(VERSCA20_IMAGE_VERSION) unchanged: no version tag on HEAD commit" ;\
	fi
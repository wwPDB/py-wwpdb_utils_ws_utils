##
# File:    ServiceDataStore.py
# Date:    6-July-2012
#
# Updates:
#          2-Aug-2016  jdw remove dependence on request object
#                          refactor to make content 'append' only.
#                          Add locking
#         23-Sep-2016  jdw adjust logging
#         15-Mar-2017  jdw increase lock timeout -
#         15-Mar-2017  jdw gut the concurrency handling wrap internal io methods
##
"""
Provide a storage interface for miscellaneous key,value data.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

try:
    import cPickle as pickle
except ImportError:
    import pickle
import os.path
import logging

from oslo_concurrency import lockutils

logger = logging.getLogger()


class ServiceDataStore(object):
    """Provide a storage interface for miscellaneous key,value data."""

    def __init__(self, sessionPath, prefix=None):
        self.__filePrefix = prefix if prefix is not None else "general"
        self.__sessionPath = sessionPath
        self.__filePath = None
        #
        lockutils.set_defaults(self.__sessionPath)
        #
        self.__setup()

    def __setup(self):
        #
        # self.__pickleProtocol = pickle.HIGHEST_PROTOCOL
        self.__pickleProtocol = 0
        try:
            self.__filePath = os.path.join(self.__sessionPath, self.__filePrefix + "-session-store.pic")
            logger.debug("Service data store path %r", self.__filePath)
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("FAILING for filePath %r", self.__filePath)

    def __serialize(self, iD):

        try:
            with open(self.__filePath, "wb") as fb:
                pickle.dump(iD, fb, self.__pickleProtocol)
            if "status" in iD:
                logger.debug("Session %s - wrote status value %r", self.__sessionPath, iD["status"])
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Serialization failure with file %s", self.__filePath)
        return False

    def __deserialize(self):
        rD = {}
        try:
            if not os.access(self.__filePath, os.R_OK):
                logger.warning("No data store in path %r ", self.__filePath)
                return rD
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        try:
            with open(self.__filePath, "rb") as fb:
                rD = pickle.load(fb)
        except Exception as e:
            logger.exception("Deserialization failure with file %s - %r", self.__filePath, str(e))

        if "status" in rD:
            logger.debug("Session %s - read dictionary %r", self.__sessionPath, rD["status"])
        return rD

    def __str__(self):
        try:
            return "\n  ".join(self.__outputList())
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def __repr__(self):
        return self.__str__()

    def dump(self, format="text"):  # pylint: disable=redefined-builtin,unused-argument
        try:
            return "\n   ".join(self.__outputList())
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def getFilePath(self):
        return self.__filePath

    #
    #  Getters()  reread before any access -
    #
    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def __outputList(self):
        rD = self.__deserialize()
        sL = []
        sL.append("Session data store contents:")
        for k in sorted(rD.keys()):
            v = rD[k]
            sL.append("     - Key: %-35s  value(s): %r" % (k, v))
        return sL

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def get(self, key):
        try:
            rD = self.__deserialize()
            return rD[key]
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def getDictionary(self):
        rD = self.__deserialize()
        return rD

    #
    #  Setters ()
    #
    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def set(self, key, value, overWrite=True):
        try:
            rD = self.__deserialize()
            if overWrite:
                rD[key] = value
                return self.__serialize(rD)
            else:
                if key not in rD:
                    rD[key] = value
                    return self.__serialize(rD)
                else:
                    # no overwrite
                    return False
        except Exception as e:
            logger.exception("Failure of set for key %r value %r error %r", key, value, str(e))
            return False

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def update(self, uDict):
        """Update (without overwrite) objects in the first level dictionary store."""
        try:
            rD = self.__deserialize()
            for k, v in uDict.items():
                if k not in rD:
                    rD[k] = v
                else:
                    # append cases - for only values of the
                    if isinstance(rD[k], list) and isinstance(v, list):
                        rD[k].extend(v)
                    elif isinstance(rD[k], list) and not isinstance(v, list):
                        rD[k].append(v)
                    elif isinstance(rD[k], dict) and isinstance(v, dict):
                        # only add new objects to a dict type.
                        for tk, tv in v:
                            if tk not in rD[k]:
                                rD[k][tk] = tv
                    else:
                        pass

            return self.__serialize(rD)
        except Exception as e:
            logger.exception("Failure for uDict %r %r", uDict, str(e))
            return False

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def updateAll(self, uDict):
        """Update with overwrite values first level dictionary store."""
        try:
            rD = self.__deserialize()
            for k, v in uDict.items():
                rD[k] = v
            if "status" in rD:
                logger.debug("Updating status value %r", rD["status"])
            return self.__serialize(rD)
        except Exception as e:
            logger.exception("Failure for uDict %r %r", uDict, str(e))
            return False

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def append(self, key, value):
        try:
            rD = self.__deserialize()
            if key not in rD:
                rD[key] = []
            rD[key].append(value)
            return self.__serialize(rD)
        except Exception as e:
            logger.exception("Failure for key %r value %r %r", key, value, str(e))
            return False

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def extend(self, key, valueList):
        try:
            rD = self.__deserialize()
            if key not in rD:
                rD[key] = []
            rD[key].extend(valueList)
            return self.__serialize(rD)
        except Exception as e:
            logger.exception("Failure for key %r value %r %r", key, valueList, str(e))
            return False

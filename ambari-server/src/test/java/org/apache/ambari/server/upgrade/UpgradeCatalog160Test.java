/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.ambari.server.upgrade;

import com.google.inject.Binder;
import com.google.inject.Guice;
import com.google.inject.Injector;
import com.google.inject.Module;
import org.apache.ambari.server.configuration.Configuration;
import org.apache.ambari.server.orm.DBAccessor;
import org.easymock.Capture;
import org.junit.Assert;
import org.junit.Test;

import java.lang.reflect.Field;
import java.sql.SQLException;
import java.util.List;

import static junit.framework.Assert.assertEquals;
import static junit.framework.Assert.assertFalse;
import static junit.framework.Assert.assertTrue;
import static junit.framework.Assert.assertNull;
import static org.easymock.EasyMock.capture;
import static org.easymock.EasyMock.createNiceMock;
import static org.easymock.EasyMock.eq;
import static org.easymock.EasyMock.expect;
import static org.easymock.EasyMock.replay;
import static org.easymock.EasyMock.verify;

/**
 * UpgradeCatalog160 unit tests.
 */
public class UpgradeCatalog160Test {

  @Test
  public void testExecuteDDLUpdates() throws Exception {

    final DBAccessor dbAccessor = createNiceMock(DBAccessor.class);
    Configuration configuration = createNiceMock(Configuration.class);
    Capture<List<DBAccessor.DBColumnInfo>> hgConfigcolumnCapture = new Capture<List<DBAccessor.DBColumnInfo>>();
    Capture<List<DBAccessor.DBColumnInfo>> viewEntitycolumnCapture = new Capture<List<DBAccessor.DBColumnInfo>>();
    Capture<DBAccessor.DBColumnInfo> restartRequiredColumnCapture = new Capture<DBAccessor.DBColumnInfo>();

    expect(configuration.getDatabaseUrl()).andReturn(Configuration.JDBC_IN_MEMORY_URL).anyTimes();

    setBPHostGroupConfigExpectations(dbAccessor, hgConfigcolumnCapture, restartRequiredColumnCapture);
    setViewEntityConfigExpectations(dbAccessor, viewEntitycolumnCapture);

    replay(dbAccessor, configuration);
    AbstractUpgradeCatalog upgradeCatalog = getUpgradeCatalog(dbAccessor);
    Class<?> c = AbstractUpgradeCatalog.class;
    Field f = c.getDeclaredField("configuration");
    f.setAccessible(true);
    f.set(upgradeCatalog, configuration);

    upgradeCatalog.executeDDLUpdates();
    verify(dbAccessor, configuration);

    assertHGConfigColumns(hgConfigcolumnCapture);
    assertViewEntityColumns(viewEntitycolumnCapture);
    assertRestartRequiredColumn(restartRequiredColumnCapture);
  }

  @Test
  public void testExecuteDMLUpdates() throws Exception {

    Configuration configuration = createNiceMock(Configuration.class);
    expect(configuration.getDatabaseUrl()).andReturn(Configuration.JDBC_IN_MEMORY_URL).anyTimes();

    final DBAccessor dbAccessor     = createNiceMock(DBAccessor.class);
    UpgradeCatalog160 upgradeCatalog = (UpgradeCatalog160) getUpgradeCatalog(dbAccessor);

    replay(dbAccessor, configuration);

    Class<?> c = AbstractUpgradeCatalog.class;
    Field f = c.getDeclaredField("configuration");
    f.setAccessible(true);
    f.set(upgradeCatalog, configuration);

    upgradeCatalog.executeDMLUpdates();

    verify(dbAccessor, configuration);
  }

  @Test
  public void testGetTargetVersion() throws Exception {
    final DBAccessor dbAccessor     = createNiceMock(DBAccessor.class);
    UpgradeCatalog   upgradeCatalog = getUpgradeCatalog(dbAccessor);

    Assert.assertEquals("1.6.0", upgradeCatalog.getTargetVersion());
  }

  private AbstractUpgradeCatalog getUpgradeCatalog(final DBAccessor dbAccessor) {
    Module module = new Module() {
      @Override
      public void configure(Binder binder) {
        binder.bind(DBAccessor.class).toInstance(dbAccessor);
      }
    };
    Injector injector = Guice.createInjector(module);
    return injector.getInstance(UpgradeCatalog160.class);
  }

  private void setBPHostGroupConfigExpectations(DBAccessor dbAccessor,
    Capture<List<DBAccessor.DBColumnInfo>> columnCapture,
    Capture<DBAccessor.DBColumnInfo> restartRequiredColumnCapture) throws SQLException {

    dbAccessor.createTable(eq("hostgroup_configuration"), capture(columnCapture),
        eq("blueprint_name"), eq("hostgroup_name"), eq("type_name"));

    dbAccessor.addColumn(eq("hostcomponentdesiredstate"),
      capture(restartRequiredColumnCapture));

    dbAccessor.addFKConstraint("hostgroup_configuration", "FK_hg_config_blueprint_name",
        "blueprint_name", "hostgroup", "blueprint_name", true);
    dbAccessor.addFKConstraint("hostgroup_configuration", "FK_hg_config_hostgroup_name",
        "hostgroup_name", "hostgroup", "name", true);
  }

  private void setViewEntityConfigExpectations(DBAccessor dbAccessor,
    Capture<List<DBAccessor.DBColumnInfo>> columnCapture) throws SQLException {

    dbAccessor.createTable(eq("viewentity"), capture(columnCapture), eq("id"));
  }

  private void assertHGConfigColumns(Capture<List<DBAccessor.DBColumnInfo>> hgConfigcolumnCapture) {
    List<DBAccessor.DBColumnInfo> columns = hgConfigcolumnCapture.getValue();
    assertEquals(4, columns.size());
    DBAccessor.DBColumnInfo column = columns.get(0);
    assertEquals("blueprint_name", column.getName());
    assertEquals(255, (int) column.getLength());
    assertEquals(String.class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());

    column = columns.get(1);
    assertEquals("hostgroup_name", column.getName());
    assertEquals(255, (int) column.getLength());
    assertEquals(String.class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());

    column = columns.get(2);
    assertEquals("type_name", column.getName());
    assertEquals(255, (int) column.getLength());
    assertEquals(String.class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());

    column = columns.get(3);
    assertEquals("config_data", column.getName());
    assertEquals(null, column.getLength());
    assertEquals(byte[].class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());
  }

  private void assertViewEntityColumns(Capture<List<DBAccessor.DBColumnInfo>> hgConfigcolumnCapture) {
    List<DBAccessor.DBColumnInfo> columns = hgConfigcolumnCapture.getValue();
    assertEquals(5, columns.size());


    columns.add(new DBAccessor.DBColumnInfo("id", Long.class, 255, null, false));
    columns.add(new DBAccessor.DBColumnInfo("view_name", String.class, 255, null, false));
    columns.add(new DBAccessor.DBColumnInfo("view_instance_name", String.class, 255, null, false));
    columns.add(new DBAccessor.DBColumnInfo("class_name", String.class, 255, null, false));
    columns.add(new DBAccessor.DBColumnInfo("id_property", String.class, 255, null, true));


    DBAccessor.DBColumnInfo column = columns.get(0);
    assertEquals("id", column.getName());
    assertNull(column.getLength());
    assertEquals(Long.class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());

    column = columns.get(1);
    assertEquals("view_name", column.getName());
    assertEquals(255, (int) column.getLength());
    assertEquals(String.class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());

    column = columns.get(2);
    assertEquals("view_instance_name", column.getName());
    assertEquals(255, (int) column.getLength());
    assertEquals(String.class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());

    column = columns.get(3);
    assertEquals("class_name", column.getName());
    assertEquals(255, (int) column.getLength());
    assertEquals(String.class, column.getType());
    assertNull(column.getDefaultValue());
    assertFalse(column.isNullable());

    column = columns.get(4);
    assertEquals("id_property", column.getName());
    assertEquals(255, (int) column.getLength());
    assertEquals(String.class, column.getType());
    assertNull(column.getDefaultValue());
    assertTrue(column.isNullable());
  }

  private void assertRestartRequiredColumn(
    Capture<DBAccessor.DBColumnInfo> restartRequiredColumnCapture) {
    DBAccessor.DBColumnInfo column = restartRequiredColumnCapture.getValue();
    assertEquals("restart_required", column.getName());
    assertEquals(1, (int) column.getLength());
    assertEquals(Boolean.class, column.getType());
    assertEquals(0, column.getDefaultValue());
    assertFalse(column.isNullable());

  }

}
